import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;

final class SimulationScene {
    static final class SceneObject {
        final String name;
        final String symbol;
        int x;
        int y;

        SceneObject(String name, String symbol, int x, int y) {
            this.name = name;
            this.symbol = symbol;
            this.x = x;
            this.y = y;
        }
    }

    private final String placeName;
    private final String subjectName;
    private final int width;
    private final int height;
    private final List<SceneObject> objects;
    private int subjectX;
    private int subjectY;
    private int activeTargetIndex;
    private final List<Integer> recentlyVisitedTargets;

    SimulationScene(String placeName, String subjectName, int width, int height) {
        this.placeName = placeName;
        this.subjectName = subjectName;
        this.width = Math.max(5, width);
        this.height = Math.max(5, height);
        this.subjectX = 1;
        this.subjectY = this.height / 2;
        this.objects = new ArrayList<>();
        this.objects.add(new SceneObject("Objeto Rojo", "R", this.width - 2, 1));
        this.objects.add(new SceneObject("Fuente de Luz", "L", this.width / 2, 1));
        this.objects.add(new SceneObject("Refugio", "H", 1, this.height - 2));
        this.objects.add(new SceneObject("Salida", "E", this.width - 2, this.height - 2));
        this.activeTargetIndex = 0;
        this.recentlyVisitedTargets = new ArrayList<>();
        rememberVisitedTarget(this.activeTargetIndex);
    }

    synchronized void updateForAction(String action) {
        String normalizedAction = action == null ? "" : action.toLowerCase(Locale.ROOT);

        int preferredTargetIndex = preferredTargetForAction(normalizedAction);
        if (preferredTargetIndex >= 0 && preferredTargetIndex != activeTargetIndex) {
            activeTargetIndex = preferredTargetIndex;
        }

        moveSubjectTowardActiveTarget();
        if (getDistanceToObjectMeters() < 0.5) {
            cycleNextTarget(normalizedAction);
        }
    }

    synchronized int getWidthCells() {
        return width;
    }

    synchronized int getHeightCells() {
        return height;
    }

    synchronized boolean moveSubjectTo(int x, int y) {
        int clampedX = clampToInteriorX(x);
        int clampedY = clampToInteriorY(y);
        if (isOccupiedByObject(clampedX, clampedY)) {
            return false;
        }
        subjectX = clampedX;
        subjectY = clampedY;
        return true;
    }

    synchronized int findObjectIndexAt(int x, int y) {
        for (int index = 0; index < objects.size(); index++) {
            SceneObject object = objects.get(index);
            if (object.x == x && object.y == y) {
                return index;
            }
        }
        return -1;
    }

    synchronized boolean moveObjectTo(int objectIndex, int x, int y) {
        if (objectIndex < 0 || objectIndex >= objects.size()) {
            return false;
        }

        int clampedX = clampToInteriorX(x);
        int clampedY = clampToInteriorY(y);

        if (subjectX == clampedX && subjectY == clampedY) {
            return false;
        }

        for (int index = 0; index < objects.size(); index++) {
            if (index == objectIndex) {
                continue;
            }
            SceneObject other = objects.get(index);
            if (other.x == clampedX && other.y == clampedY) {
                return false;
            }
        }

        SceneObject object = objects.get(objectIndex);
        object.x = clampedX;
        object.y = clampedY;
        return true;
    }

    private void cycleNextTarget(String normalizedAction) {
        int current = activeTargetIndex;
        rememberVisitedTarget(current);

        int preferred = preferredTargetForAction(normalizedAction);
        if (preferred >= 0 && preferred != current && !recentlyVisitedTargets.contains(preferred)) {
            this.activeTargetIndex = preferred;
            System.out.println("[ESCENA] Objetivo alcanzado. Reorientando foco a: " + getActiveTarget().name);
            return;
        }

        int next = chooseNovelTarget(current);
        this.activeTargetIndex = next;
        System.out.println("[ESCENA] Objetivo alcanzado. Nuevo foco adaptativo: " + getActiveTarget().name);
    }

    private int chooseNovelTarget(int current) {
        List<Integer> candidates = new ArrayList<>();
        Set<Integer> blocked = new HashSet<>(recentlyVisitedTargets);

        for (int index = 0; index < objects.size(); index++) {
            if (index == current) {
                continue;
            }
            if (!blocked.contains(index)) {
                candidates.add(index);
            }
        }

        if (candidates.isEmpty()) {
            for (int index = 0; index < objects.size(); index++) {
                if (index != current) {
                    candidates.add(index);
                }
            }
        }

        if (candidates.isEmpty()) {
            return current;
        }

        int randomIndex = ThreadLocalRandom.current().nextInt(candidates.size());
        return candidates.get(randomIndex);
    }

    private void rememberVisitedTarget(int index) {
        if (recentlyVisitedTargets.isEmpty() || recentlyVisitedTargets.get(recentlyVisitedTargets.size() - 1) != index) {
            recentlyVisitedTargets.add(index);
        }
        while (recentlyVisitedTargets.size() > 2) {
            recentlyVisitedTargets.remove(0);
        }
    }

    private int preferredTargetForAction(String normalizedAction) {
        if (normalizedAction.contains("buscar refugio")) {
            return indexOfObject("Refugio");
        }
        if (normalizedAction.contains("explorar")
                || normalizedAction.contains("avanzar")
                || normalizedAction.contains("caminar")) {
            // Explorar no siempre significa salida: introduce exploracion menos mecanica.
            if (ThreadLocalRandom.current().nextDouble() < 0.35) {
                return indexOfObject("Objeto Rojo");
            }
            return indexOfObject("Salida");
        }
        if (normalizedAction.contains("examinar")) {
            return indexOfObject("Objeto Rojo");
        }
        if (normalizedAction.contains("observar")) {
            return indexOfObject("Fuente de Luz");
        }
        return -1;
    }

    private int indexOfObject(String objectName) {
        for (int index = 0; index < objects.size(); index++) {
            if (objects.get(index).name.equals(objectName)) {
                return index;
            }
        }
        return 0;
    }

    private void moveSubjectTowardActiveTarget() {
        SceneObject target = objects.get(activeTargetIndex);
        if (subjectX < target.x) {
            subjectX++;
        } else if (subjectX > target.x) {
            subjectX--;
        }

        if (subjectY < target.y) {
            subjectY++;
        } else if (subjectY > target.y) {
            subjectY--;
        }

        subjectX = clampToInteriorX(subjectX);
        subjectY = clampToInteriorY(subjectY);
    }

    private int clampToInteriorX(int x) {
        return Math.max(1, Math.min(width - 2, x));
    }

    private int clampToInteriorY(int y) {
        return Math.max(1, Math.min(height - 2, y));
    }

    private boolean isOccupiedByObject(int x, int y) {
        for (SceneObject object : objects) {
            if (object.x == x && object.y == y) {
                return true;
            }
        }
        return false;
    }

    synchronized String getPlaceName() {
        return placeName;
    }

    synchronized String getSubjectName() {
        return subjectName;
    }

    synchronized String getLightLevel() {
        if (subjectX <= width / 3) {
            return "Bajo";
        }
        if (subjectX <= (2 * width) / 3) {
            return "Medio";
        }
        return "Alto";
    }

    synchronized double getDistanceToObjectMeters() {
        SceneObject target = objects.get(activeTargetIndex);
        double dx = target.x - subjectX;
        double dy = target.y - subjectY;
        double gridDistance = Math.sqrt((dx * dx) + (dy * dy));
        return Math.max(0.15, gridDistance * 0.75);
    }

    synchronized SceneObject getActiveTarget() {
        return objects.get(activeTargetIndex);
    }

    synchronized List<SceneObject> getObjects() {
        return Collections.unmodifiableList(new ArrayList<>(objects));
    }

    synchronized int getSubjectX() {
        return subjectX;
    }

    synchronized int getSubjectY() {
        return subjectY;
    }

    synchronized String render() {
        StringBuilder builder = new StringBuilder();
        builder.append(String.format(Locale.US,
                "[ESCENA] Lugar=%s | Sujeto=%s | Objetivo=%s | Luz=%s | Distancia=%.2f m\n",
                placeName,
                subjectName,
                getActiveTarget().name,
                getLightLevel(),
                getDistanceToObjectMeters()));

        builder.append('+');
        for (int x = 0; x < width; x++) {
            builder.append('-');
        }
        builder.append('+').append('\n');

        for (int y = 0; y < height; y++) {
            builder.append('|');
            for (int x = 0; x < width; x++) {
                char cell = '.';
                if (x == subjectX && y == subjectY) {
                    cell = 'S';
                } else {
                    for (SceneObject object : objects) {
                        if (object.x == x && object.y == y) {
                            cell = object.symbol.charAt(0);
                            break;
                        }
                    }
                }
                builder.append(cell);
            }
            builder.append('|').append('\n');
        }

        builder.append('+');
        for (int x = 0; x < width; x++) {
            builder.append('-');
        }
        builder.append('+').append('\n');
        builder.append("S=sujeto | R=objeto rojo | L=fuente de luz | H=refugio | E=salida\n");
        return builder.toString();
    }
}