import java.io.IOException;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Locale;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicReference;

public class CharacterBody implements Runnable {
    private static final int TELEMETRY_PERIOD_MS = 16;
    private static final String TELEMETRY_TARGET_IP = "127.0.0.1";
    private static final int TELEMETRY_TARGET_PORT = 5051;

    private final AtomicReference<String> currentAction;
    private final CognitiveSocketBridge cognitiveBridge;
    private final SimulationScene simulationScene;
    private volatile SimulationWindow simulationWindow;
    private final AffectiveTelemetryUDP telemetryOut;
    private volatile boolean telemetryRunning;
    private Thread telemetryThread;
    private final Deque<ActionEvent> recentActionEvents;
    private final int actionHistoryWindow = 12;
    private long actionCycleCounter;
    private static final double BETA_VELOCIDAD = 0.25;
    private final AtomicReference<Double> agentValence;
    private final AtomicReference<String> agentState;
    private final AtomicReference<Double> motorOutput;
    private final AtomicReference<Double> sensorSensitivity;

    private static final class ActionEvent {
        private final String action;
        private final long cycle;

        private ActionEvent(String action, long cycle) {
            this.action = action;
            this.cycle = cycle;
        }
    }

    public CharacterBody(CognitiveSocketBridge cognitiveBridge) {
        this.currentAction = new AtomicReference<>("INACTIVO");
        this.cognitiveBridge = cognitiveBridge;
        this.simulationScene = new SimulationScene("Sala Principal del Laboratorio Hart", "Sujeto-01", 13, 7);
        this.telemetryOut = createTelemetryChannel();
        this.telemetryRunning = false;
        this.recentActionEvents = new ArrayDeque<>();
        this.actionCycleCounter = 0L;
        this.agentValence = new AtomicReference<>(0.0);
        this.agentState = new AtomicReference<>("neutral");
        this.motorOutput = new AtomicReference<>(1.0);
        this.sensorSensitivity = new AtomicReference<>(1.0);
        System.out.println("[BODY INIT] Cuerpo fisico instanciado y listo para recibir comandos.");
    }

    private AffectiveTelemetryUDP createTelemetryChannel() {
        try {
            return new AffectiveTelemetryUDP(TELEMETRY_TARGET_IP, TELEMETRY_TARGET_PORT);
        } catch (IOException e) {
            System.out.println("[TELEMETRIA] No fue posible iniciar UDP expresivo: " + e.getMessage());
            return null;
        }
    }

    public void attachWindow(SimulationWindow simulationWindow) {
        this.simulationWindow = simulationWindow;
    }

    public void startTelemetryEmitter() {
        if (telemetryOut == null || telemetryThread != null) {
            return;
        }

        telemetryRunning = true;
        telemetryThread = new Thread(() -> {
            while (telemetryRunning && !Thread.currentThread().isInterrupted()) {
                float valence = agentValence.get().floatValue();
                float motor = motorOutput.get().floatValue();
                float fov = sensorSensitivity.get().floatValue();
                float shiver = valence < -0.3f ? Math.min(1.0f, Math.abs(valence) * 0.8f) : 0.0f;

                telemetryOut.broadcastExpressiveState(valence, motor, fov, shiver);

                try {
                    Thread.sleep(TELEMETRY_PERIOD_MS);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "AffectiveTelemetryThread");
        telemetryThread.setDaemon(true);
        telemetryThread.start();
    }

    public void stopTelemetryEmitter() {
        telemetryRunning = false;
        if (telemetryThread != null) {
            telemetryThread.interrupt();
            telemetryThread = null;
        }
    }

    public void closeResources() {
        stopTelemetryEmitter();
        if (telemetryOut != null) {
            telemetryOut.close();
        }
    }

    public void receiveCognitiveCommand(String command) {
        String normalizedCommand = normalizeCommand(command);
        currentAction.set(normalizedCommand);

        // Track recent action timeline for saturation (count + temporal persistence)
        if (!normalizedCommand.equals("INACTIVO")) {
            synchronized (recentActionEvents) {
                actionCycleCounter++;
                if (recentActionEvents.size() == actionHistoryWindow) {
                    recentActionEvents.removeFirst();
                }
                recentActionEvents.addLast(new ActionEvent(normalizedCommand, actionCycleCounter));
            }
        }
        System.out.println("[CHARACTER BODY] Ejecutando comando fisico: [" + normalizedCommand + "]");
    }

    public SensoryData getSensoryInput() {
        double valence = agentValence.get();
        
        // Modulación de Percepción: FOV adaptativo basado en Valencia y sensorSensitivity
        // Alta Curiosidad (valence > 0.5): Amplía el radio de detección (FOV expandido)
        // Alta Ansiedad (valence < -0.5): Restringe el foco (túnel atencional)
        double perceptionModifier = (1.0 + (valence * 0.3)) * sensorSensitivity.get(); // rango: 0.42 a 1.69

        String simulatedLight = simulationScene.getLightLevel();
        double actualDistance = simulationScene.getDistanceToObjectMeters();
        double simulatedProximity = Math.max(0.15, actualDistance / perceptionModifier);

        return new SensoryData(simulatedLight, simulatedProximity);
    }

    public String getCurrentAction() {
        return currentAction.get();
    }

    private String normalizeCommand(String command) {
        if (command == null) {
            return "INACTIVO";
        }

        String trimmedCommand = command.trim();
        return trimmedCommand.isEmpty() ? "INACTIVO" : trimmedCommand;
    }

    private CognitiveSocketBridge.BridgeCommand resolveBridgeCommand(SensoryData perception) {
        if (cognitiveBridge == null) {
            return null;
        }

        try {
            if (!cognitiveBridge.reconnectIfNeeded(250L)) {
                return null;
            }

            return cognitiveBridge.requestCommand(perception, getCurrentAction());
        } catch (IOException e) {
            System.out.println("[BRIDGE] La comunicacion con Python fallo. Se aplicara heuristica local: "
                    + e.getMessage());
            return null;
        }
    }

    private String decideFallbackCommand(SensoryData perception) {
        double valence = agentValence.get();
        String state = agentState.get();
        
        // Modulación de acciones basada en Valencia (Opción B: Bidireccional)
        // Valencia Alta (>0.5): Arriesgado, explora agresivamente
        // Valencia Baja (<-0.3): Defensivo, busca seguridad
        
        if ("Alto".equals(perception.getLightLevel())
                && perception.getProximityToObjectMeters() < 1.0) {
            if (valence > 0.5) {
                return "Explorar con confianza y curiosidad extrema";
            } else if (valence < -0.3) {
                return "Examinar objeto rojo con cautela defensiva";
            } else {
                return "Examinar objeto rojo con curiosidad intensa";
            }
        }

        if ("Bajo".equals(perception.getLightLevel())
                && perception.getProximityToObjectMeters() > 3.0) {
            if (valence < -0.5) {
                return "Buscar refugio seguro inmediatamente";
            } else if (valence > 0.3) {
                return "Avanzar explorando la oscuridad";
            } else {
                return "Caminar lentamente buscando una fuente de iluminacion";
            }
        }

        if ("Medio".equals(perception.getLightLevel())) {
            if (valence > 0.5) {
                return "Explorar el entorno con paso confiado";
            } else if (valence < -0.3) {
                return "Mantener posicion defensiva";
            } else {
                return "Observar entorno con calma y reflexion";
            }
        }

        // Fallback: si estado defensivo extremo, buscar seguridad
        if (valence < -0.7) {
            return "Mantener posicion actual y evaluar amenazas";
        }

        return "Mantener posicion actual";
    }

    private FeedbackData evaluateAffectiveFeedback(String action, SensoryData perception) {
        double affectiveChange;
        String rationale;

        if (action.contains("Examinar") && "Alto".equals(perception.getLightLevel())) {
            affectiveChange = 0.30;
            rationale = "La exploracion cercana bajo alta iluminacion incrementa curiosidad y agencia.";
        } else if (action.contains("Caminar lentamente")
                && "Bajo".equals(perception.getLightLevel())) {
            affectiveChange = -0.12;
            rationale = "La navegacion cautelosa en baja luz incrementa tension y vigilancia.";
        } else if (action.contains("Observar entorno")) {
            affectiveChange = 0.08;
            rationale = "La observacion deliberada estabiliza el estado afectivo y reduce ruido interno.";
        } else {
            affectiveChange = 0.0;
            rationale = "La accion no altera significativamente la valencia afectiva del cuerpo.";
        }

        // Behavioral saturation: attenuate using repetition + temporal persistence + beta velocity
        double saturationFactor = computeSaturationFactor(action);
        double attenuatedChange = affectiveChange * saturationFactor;
        String satMsg = saturationFactor < 1.0 ? String.format(Locale.US, " (SATURADO x%.2f)", saturationFactor) : "";

        System.out.println(String.format(Locale.US,
                "[BODY FEEDBACK] action=%s | affectiveChange=%.2f | rationale=%s%s",
                action,
                attenuatedChange,
                rationale,
                satMsg));

        return new FeedbackData(action, attenuatedChange, rationale + satMsg);
    }

    // Compute saturation using repetition (N), temporal persistence (cycle gaps), and switchRate.
    // High switchRate lowers fatigue because active exploration is less emotionally saturating.
    private double computeSaturationFactor(String action) {
        synchronized (recentActionEvents) {
            if (recentActionEvents.isEmpty()) {
                return 1.0;
            }

            int repeatCount = 0;
            long lastCycle = -1L;
            long gapSum = 0L;
            int gapCount = 0;

            int transitions = 0;
            int possibleTransitions = Math.max(0, recentActionEvents.size() - 1);
            String prevAction = null;

            for (ActionEvent event : recentActionEvents) {
                if (prevAction != null && !prevAction.equals(event.action)) {
                    transitions++;
                }
                prevAction = event.action;

                if (event.action.equals(action)) {
                    repeatCount++;
                    if (lastCycle >= 0L) {
                        gapSum += (event.cycle - lastCycle);
                        gapCount++;
                    }
                    lastCycle = event.cycle;
                }
            }

            if (repeatCount <= 1) {
                return 1.0;
            }

            double switchRate = possibleTransitions == 0 ? 0.0 : (double) transitions / possibleTransitions;
            double betaContextual = clamp01(1.0 - BETA_VELOCIDAD * switchRate);

            // Count-based fatigue: same action repeated more than twice.
            double repetitionPenalty = Math.max(0, repeatCount - 2) * 0.25;

            // Temporal persistence: repetitions separated by many cycles still indicate sustained fixation.
            double avgGap = gapCount == 0 ? 1.0 : (double) gapSum / gapCount;
            double temporalPersistence = clamp01((avgGap - 1.0) / 4.0); // gap=1 -> 0, gap=5+ -> 1
            double temporalPenalty = temporalPersistence * 0.20;

            double totalPenalty = (repetitionPenalty + temporalPenalty) * betaContextual;
            double factor = 1.0 - totalPenalty;
            return Math.max(0.15, Math.min(1.0, factor));
        }
    }

    private double clamp01(double value) {
        if (value < 0.0) {
            return 0.0;
        }
        if (value > 1.0) {
            return 1.0;
        }
        return value;
    }

    private void publishFeedback(CognitiveSocketBridge.BridgeCommand bridgeCommand,
            SensoryData perception,
            FeedbackData feedback) {
        if (bridgeCommand == null || cognitiveBridge == null) {
            return;
        }

        try {
            cognitiveBridge.sendFeedback(bridgeCommand.getSequence(), perception, feedback);
        } catch (IOException e) {
            System.out.println("[BRIDGE] No fue posible enviar feedback afectivo a Python: "
                    + e.getMessage());
        }
    }

    @Override
    public void run() {
        System.out.println("================= CHARACTER BODY HILO INICIADO =================");

        while (!Thread.currentThread().isInterrupted()) {
            SensoryData perception = getSensoryInput();
            CognitiveSocketBridge.BridgeCommand bridgeCommand;
            String command;

            System.out.println("[BODY LOOP] Percepcion recibida: " + perception);

            bridgeCommand = resolveBridgeCommand(perception);
            
            // Actualizar estado afectivo del agente desde el comando Python
            if (bridgeCommand != null) {
                agentValence.set(bridgeCommand.getAffectiveValence());
                agentState.set(bridgeCommand.getAgentState());
                System.out.println(String.format(Locale.US,
                        "[BODY STATE] Valencia=%.2f | EstadoAgente=%s",
                        bridgeCommand.getAffectiveValence(),
                        bridgeCommand.getAgentState()));
            }
            // Actualizar moduladores de resiliencia
            if (bridgeCommand != null) {
                motorOutput.set(bridgeCommand.getMotorOutput());
                sensorSensitivity.set(bridgeCommand.getSensorSensitivity());
                System.out.println(String.format(Locale.US,
                        "[RESILIENCE] MotorOutput=%.2f | SensorSensitivity=%.2f",
                        bridgeCommand.getMotorOutput(),
                        bridgeCommand.getSensorSensitivity()));
            }
            
            command = bridgeCommand != null ? bridgeCommand.getCommand() : decideFallbackCommand(perception);

            receiveCognitiveCommand(command);
            simulationScene.updateForAction(command);
            if (simulationWindow != null) {
                simulationWindow.repaintScene();
            }
            publishFeedback(bridgeCommand, perception, evaluateAffectiveFeedback(command, perception));

            try {
                // Modulate processing speed with motorOutput
                // motorOutput 0.3 (paralyzed) → longer sleep; motorOutput 1.5 (hyperkinetic) → shorter sleep
                double motor = motorOutput.get();
                long baseDelay = 200L;
                long variableDelay = ThreadLocalRandom.current().nextLong(350L);
                long adjustedDelay = (long) ((baseDelay + variableDelay) / motor);
                Thread.sleep(adjustedDelay);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                System.out.println("[BODY LOOP] Hilo interrumpido correctamente por un comando externo.");
                break;
            }
        }
    }

    public static void main(String[] args) {
        int port = parsePort(args);

        System.out.println("**********************************************");
        System.out.println("* INICIANDO EL SISTEMA HART CONSCIOUSNESS MODEL *");
        System.out.println("**********************************************");

        CognitiveSocketBridge bridge = null;
        CharacterBody character = null;
        try {
            bridge = new CognitiveSocketBridge(port);
            System.out.println("[BRIDGE] Servidor TCP iniciado en localhost:" + bridge.getPort() + ".");
            System.out.println("[BRIDGE] Esperando cliente Python durante 30 segundos...");

            if (bridge.awaitClient(30_000L)) {
                System.out.println("[BRIDGE] Cliente Python conectado. El control cognitivo remoto esta activo.");
            } else {
                System.out.println("[BRIDGE] No llego cliente Python. Se iniciara en modo autonomo y se aceptaran reconexiones.");
            }

            character = new CharacterBody(bridge);
            SimulationWindow simulationWindow = new SimulationWindow(character.simulationScene);
            character.attachWindow(simulationWindow);
            character.startTelemetryEmitter();
            simulationWindow.show();
            Thread bodySimulator = new Thread(character, "CharacterBodyThread");

            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("[MAIN THREAD] Shutdown hook activado. Deteniendo CharacterBody...");
                bodySimulator.interrupt();
                try {
                    bodySimulator.join(2_000L);
                } catch (InterruptedException ignored) {
                    Thread.currentThread().interrupt();
                }
            }, "CharacterBodyShutdownHook"));

            bodySimulator.start();
            System.out.println("[MAIN THREAD] CharacterBody en ejecucion continua. Usa Ctrl+C para detener.");

            try {
                bodySimulator.join();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                bodySimulator.interrupt();
            }
        } catch (IOException e) {
            System.out.println("[BRIDGE] No fue posible iniciar el servidor TCP: " + e.getMessage());
        } finally {
            if (character != null) {
                character.closeResources();
            }
            if (bridge != null) {
                try {
                    bridge.close();
                } catch (IOException e) {
                    System.out.println("[BRIDGE] Error al cerrar el socket: " + e.getMessage());
                }
            }
        }

        System.out.println("[MAIN THREAD] Simulacion terminada con exito y limpieza total.");
    }

    private static int parsePort(String[] args) {
        if (args.length == 0) {
            return 5050;
        }

        try {
            return Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.out.println("[MAIN THREAD] Puerto invalido. Se utilizara el puerto 5050 por defecto.");
            return 5050;
        }
    }
}