import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.List;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;

final class SimulationWindow {
    private final ScenePanel panel;

    SimulationWindow(SimulationScene scene) {
        this.panel = new ScenePanel(scene);
    }

    void show() {
        SwingUtilities.invokeLater(() -> {
            JFrame frame = new JFrame("HART - Sujeto y Entorno");
            frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
            frame.setLayout(new BorderLayout());
            frame.add(panel, BorderLayout.CENTER);
            frame.pack();
            frame.setLocationRelativeTo(null);
            frame.setVisible(true);
        });
    }

    void repaintScene() {
        SwingUtilities.invokeLater(panel::repaint);
    }

    private static final class ScenePanel extends JPanel {
        private final SimulationScene scene;
        private final int cellSize = 44;
        private static final int topHudHeight = 64;
        private int draggingObjectIndex = -1;
        private boolean draggingSubject = false;

        private ScenePanel(SimulationScene scene) {
            this.scene = scene;
            setPreferredSize(new Dimension(720, 560));
            setBackground(new Color(15, 16, 20));
            installMouseInteractions();
        }

        private void installMouseInteractions() {
            MouseAdapter adapter = new MouseAdapter() {
                @Override
                public void mousePressed(MouseEvent event) {
                    int gridX = toGridX(event.getX());
                    int gridY = toGridY(event.getY());
                    if (!isInsideGrid(gridX, gridY)) {
                        return;
                    }

                    if (scene.getSubjectX() == gridX && scene.getSubjectY() == gridY) {
                        draggingSubject = true;
                        draggingObjectIndex = -1;
                        return;
                    }

                    draggingObjectIndex = scene.findObjectIndexAt(gridX, gridY);
                    draggingSubject = false;
                }

                @Override
                public void mouseDragged(MouseEvent event) {
                    int gridX = toGridX(event.getX());
                    int gridY = toGridY(event.getY());
                    if (!isInsideGrid(gridX, gridY)) {
                        return;
                    }

                    if (draggingSubject) {
                        scene.moveSubjectTo(gridX, gridY);
                        repaint();
                        return;
                    }

                    if (draggingObjectIndex >= 0) {
                        scene.moveObjectTo(draggingObjectIndex, gridX, gridY);
                        repaint();
                    }
                }

                @Override
                public void mouseReleased(MouseEvent event) {
                    draggingSubject = false;
                    draggingObjectIndex = -1;
                }
            };

            addMouseListener(adapter);
            addMouseMotionListener(adapter);
        }

        private int toGridX(int pixelX) {
            return (pixelX - getGridOriginX()) / cellSize;
        }

        private int toGridY(int pixelY) {
            return (pixelY - getGridOriginY()) / cellSize;
        }

        private int getGridOriginX() {
            int gridWidth = scene.getWidthCells() * cellSize;
            return (getWidth() - gridWidth) / 2;
        }

        private int getGridOriginY() {
            int gridHeight = scene.getHeightCells() * cellSize;
            int availableHeight = getHeight() - topHudHeight;
            return topHudHeight + Math.max(0, (availableHeight - gridHeight) / 2);
        }

        private boolean isInsideGrid(int gridX, int gridY) {
            return gridX >= 0 && gridX < scene.getWidthCells() && gridY >= 0 && gridY < scene.getHeightCells();
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            super.paintComponent(graphics);
            Graphics2D g2 = (Graphics2D) graphics.create();
            try {
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                int originX = getGridOriginX();
                int originY = getGridOriginY();

                drawHUD(g2);

                g2.setColor(new Color(70, 74, 90));
                g2.fillRoundRect(
                        originX - 12,
                        originY - 18,
                        scene.getWidthCells() * cellSize + 24,
                        scene.getHeightCells() * cellSize + 36,
                        18,
                        18);

                drawGrid(g2, originX, originY);
                drawObjects(g2, originX, originY);
                drawSubject(g2, originX, originY);
            } finally {
                g2.dispose();
            }
        }

        private void drawHUD(Graphics2D g2) {
            g2.setColor(new Color(24, 26, 34, 220));
            g2.fillRoundRect(10, 10, getWidth() - 20, topHudHeight - 16, 14, 14);

            g2.setFont(new Font("Monospaced", Font.BOLD, 16));
            g2.setColor(new Color(255, 255, 255, 220));
            SimulationScene.SceneObject target = scene.getActiveTarget();
            String targetName = target != null ? target.name : "Desconocido";
            g2.drawString("OBJETIVO ACTIVO: " + targetName.toUpperCase(), 20, 34);

            g2.setFont(new Font("Monospaced", Font.PLAIN, 12));
            g2.setColor(new Color(200, 202, 210));
            g2.drawString("Arrastra S, R, L, H o E para alterar el entorno en tiempo real.", 20, 52);
        }

        private void drawGrid(Graphics2D g2, int originX, int originY) {
            g2.setColor(new Color(90, 95, 112));
            for (int row = 0; row < scene.getHeightCells(); row++) {
                for (int col = 0; col < scene.getWidthCells(); col++) {
                    int x = originX + (col * cellSize);
                    int y = originY + (row * cellSize);
                    g2.drawRoundRect(x, y, cellSize - 4, cellSize - 4, 10, 10);
                }
            }
        }

        private void drawObjects(Graphics2D g2, int originX, int originY) {
            List<SimulationScene.SceneObject> objects = scene.getObjects();
            SimulationScene.SceneObject activeTarget = scene.getActiveTarget();
            for (SimulationScene.SceneObject object : objects) {
                int cellX = originX + (object.x * cellSize);
                int cellY = originY + (object.y * cellSize);

                if (activeTarget != null && object == activeTarget) {
                    g2.setColor(new Color(255, 255, 255, 56));
                    g2.fillRoundRect(cellX, cellY, cellSize, cellSize, 12, 12);
                    g2.setColor(Color.WHITE);
                    g2.drawRoundRect(cellX, cellY, cellSize, cellSize, 12, 12);
                }

                if ("R".equals(object.symbol)) {
                    g2.setColor(new Color(236, 79, 79));
                } else if ("L".equals(object.symbol)) {
                    g2.setColor(new Color(244, 201, 80));
                } else if ("H".equals(object.symbol)) {
                    g2.setColor(new Color(88, 170, 118));
                } else {
                    g2.setColor(new Color(89, 152, 244));
                }

                g2.fillRoundRect(cellX + 6, cellY + 6, cellSize - 12, cellSize - 12, 8, 8);
                g2.setColor(Color.WHITE);
                g2.setFont(new Font("SansSerif", Font.BOLD, 14));
                g2.drawString(object.symbol, cellX + 18, cellY + 28);
            }
        }

        private void drawSubject(Graphics2D g2, int originX, int originY) {
            int x = originX + (scene.getSubjectX() * cellSize);
            int y = originY + (scene.getSubjectY() * cellSize);

            g2.setColor(new Color(182, 95, 246));
            g2.fillOval(x + 6, y + 6, cellSize - 16, cellSize - 16);
            g2.setColor(Color.WHITE);
            g2.drawOval(x + 6, y + 6, cellSize - 16, cellSize - 16);
            g2.drawString("S", x + 16, y + 27);
        }
    }
}