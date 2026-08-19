import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;

class CognitiveSocketBridge implements Closeable {
    private static final Gson GSON = new Gson();

    private final ServerSocket serverSocket;
    private Socket clientSocket;
    private BufferedReader reader;
    private BufferedWriter writer;
    private long sequenceCounter;

    public CognitiveSocketBridge(int port) throws IOException {
        this.serverSocket = new ServerSocket(port);
        this.sequenceCounter = 0L;
    }

    public int getPort() {
        return serverSocket.getLocalPort();
    }

    public boolean awaitClient(long timeoutMillis) throws IOException {
        disconnectClient();
        return acceptClient(timeoutMillis);
    }

    public boolean reconnectIfNeeded(long timeoutMillis) throws IOException {
        if (isConnected()) {
            return true;
        }

        return acceptClient(timeoutMillis);
    }

    private boolean acceptClient(long timeoutMillis) throws IOException {
        serverSocket.setSoTimeout((int) Math.min(Integer.MAX_VALUE, timeoutMillis));

        try {
            clientSocket = serverSocket.accept();
            clientSocket.setTcpNoDelay(true);
            reader = new BufferedReader(
                    new InputStreamReader(clientSocket.getInputStream(), StandardCharsets.UTF_8));
            writer = new BufferedWriter(
                    new OutputStreamWriter(clientSocket.getOutputStream(), StandardCharsets.UTF_8));
            return true;
        } catch (SocketTimeoutException e) {
            return false;
        } finally {
            serverSocket.setSoTimeout(0);
        }
    }

    public boolean isConnected() {
        return clientSocket != null && clientSocket.isConnected() && !clientSocket.isClosed();
    }

    public synchronized BridgeCommand requestCommand(SensoryData perception, String currentAction)
            throws IOException {
        if (!isConnected()) {
            return null;
        }

        long sequence = sequenceCounter++;
        writeMessage(new PerceptionMessage(
                "perception",
                sequence,
                perception.getLightLevel(),
                perception.getProximityToObjectMeters(),
                currentAction));

        CommandResponse response = readMessage(CommandResponse.class);
        if (response == null || response.command == null) {
            return null;
        }

        if (!"command".equals(response.type) || response.sequence != sequence) {
            throw new IOException("Respuesta fuera de protocolo desde Python.");
        }

        String normalizedCommand = response.command.trim();
        double valence = response.affectiveValence != null ? response.affectiveValence : 0.0;
        double momentum = response.affectiveMomentum != null ? response.affectiveMomentum : 0.0;
        String state = response.agentState != null ? response.agentState : "neutral";
        double motor = response.motorOutput != null ? response.motorOutput : 1.0;
        double sensor = response.sensorSensitivity != null ? response.sensorSensitivity : 1.0;
        return normalizedCommand.isEmpty() ? null : new BridgeCommand(sequence, normalizedCommand, valence, momentum, state, motor, sensor);
    }

    public synchronized void sendFeedback(long sequence, SensoryData perception, FeedbackData feedback)
            throws IOException {
        if (!isConnected()) {
            return;
        }

        writeMessage(new FeedbackMessage(
                "feedback",
                sequence,
                perception.getLightLevel(),
                perception.getProximityToObjectMeters(),
                feedback.getActionTaken(),
                feedback.getAffectiveChange(),
                feedback.getRationale()));
    }

    private void writeMessage(Object payload) throws IOException {
        writer.write(GSON.toJson(payload));
        writer.write('\n');
        writer.flush();
    }

    private <T> T readMessage(Class<T> targetType) throws IOException {
        String rawPayload = reader.readLine();
        if (rawPayload == null) {
            disconnectClient();
            return null;
        }

        try {
            return GSON.fromJson(rawPayload, targetType);
        } catch (JsonSyntaxException e) {
            throw new IOException("JSON invalido recibido desde Python.", e);
        }
    }

    private void disconnectClient() throws IOException {
        if (reader != null) {
            reader.close();
            reader = null;
        }

        if (writer != null) {
            writer.close();
            writer = null;
        }

        if (clientSocket != null) {
            clientSocket.close();
            clientSocket = null;
        }
    }

    @Override
    public void close() throws IOException {
        disconnectClient();
        serverSocket.close();
    }

    static final class BridgeCommand {
        private final long sequence;
        private final String command;
        private final double affectiveValence;
        private final double affectiveMomentum;
        private final String agentState;

        private final double motorOutput;
        private final double sensorSensitivity;

        BridgeCommand(long sequence, String command, double affectiveValence, double affectiveMomentum, String agentState, double motorOutput, double sensorSensitivity) {
            this.sequence = sequence;
            this.command = command;
            this.affectiveValence = affectiveValence;
            this.affectiveMomentum = affectiveMomentum;
            this.agentState = agentState;
            this.motorOutput = motorOutput;
            this.sensorSensitivity = sensorSensitivity;
        }

        long getSequence() {
            return sequence;
        }

        String getCommand() {
            return command;
        }

        double getAffectiveValence() {
            return affectiveValence;
        }

        double getAffectiveMomentum() {
            return affectiveMomentum;
        }

        String getAgentState() {
            return agentState;
        }

        double getMotorOutput() {
            return motorOutput;
        }

        double getSensorSensitivity() {
            return sensorSensitivity;
        }
    }

    private static final class PerceptionMessage {
        private final String type;
        private final long sequence;
        private final String lightLevel;
        private final double proximityToObjectMeters;
        private final String currentAction;

        private PerceptionMessage(String type,
                long sequence,
                String lightLevel,
                double proximityToObjectMeters,
                String currentAction) {
            this.type = type;
            this.sequence = sequence;
            this.lightLevel = lightLevel;
            this.proximityToObjectMeters = proximityToObjectMeters;
            this.currentAction = currentAction;
        }
    }

    private static final class CommandResponse {
        private String type;
        private long sequence;
        private String command;
        private Double affectiveValence;
        private Double affectiveMomentum;
        private String agentState;
        private Double motorOutput;
        private Double sensorSensitivity;
    }

    private static final class FeedbackMessage {
        private final String type;
        private final long sequence;
        private final String lightLevel;
        private final double proximityToObjectMeters;
        private final String actionTaken;
        private final double affectiveChange;
        private final String rationale;

        private FeedbackMessage(String type,
                long sequence,
                String lightLevel,
                double proximityToObjectMeters,
                String actionTaken,
                double affectiveChange,
                String rationale) {
            this.type = type;
            this.sequence = sequence;
            this.lightLevel = lightLevel;
            this.proximityToObjectMeters = proximityToObjectMeters;
            this.actionTaken = actionTaken;
            this.affectiveChange = affectiveChange;
            this.rationale = rationale;
        }
    }
}