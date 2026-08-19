import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class AffectiveTelemetryUDP implements AutoCloseable {
    private final DatagramSocket socket;
    private final InetAddress targetAddress;
    private final int targetPort;
    private final ByteBuffer buffer;

    public AffectiveTelemetryUDP(String targetIp, int targetPort) throws IOException {
        this.socket = new DatagramSocket();
        this.targetAddress = InetAddress.getByName(targetIp);
        this.targetPort = targetPort;
        this.buffer = ByteBuffer.allocate(16);
        this.buffer.order(ByteOrder.LITTLE_ENDIAN);
        System.out.println("[TELEMETRIA] Canal expresivo UDP listo -> " + targetIp + ":" + targetPort);
    }

    public void broadcastExpressiveState(float valence, float motorOutput, float fovMultiplier, float anxietyShiver) {
        if (socket.isClosed()) {
            return;
        }

        buffer.clear();
        buffer.putFloat(valence);
        buffer.putFloat(motorOutput);
        buffer.putFloat(fovMultiplier);
        buffer.putFloat(anxietyShiver);

        byte[] payload = buffer.array();
        DatagramPacket packet = new DatagramPacket(payload, payload.length, targetAddress, targetPort);

        try {
            socket.send(packet);
        } catch (IOException ignored) {
            // UDP: los frames pueden perderse sin afectar el canal cognitivo.
        }
    }

    @Override
    public void close() {
        socket.close();
    }

    public int getTargetPort() {
        return targetPort;
    }
}