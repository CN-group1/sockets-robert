import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;

/**
 * UDP client for the lab server protocol:
 * - UTF-8 datagrams
 * - payload contains sequence id, e.g. "42" or "MSG 42"
 *
 * Usage:
 *   javac client/UdpClient.java
 *   java -cp client UdpClient --host <SERVER_IP> --port 5001
 *   java -cp client UdpClient --host <SERVER_IP> --port 5001 --start 1 --count 100 --prefix "MSG "
 */
public final class UdpClient {
    private static final int DEFAULT_PORT = 5001;
    private static final int DEFAULT_START = 1;
    private static final int DEFAULT_COUNT = 100;
    private static final int DEFAULT_DELAY_MS = 10;

    private UdpClient() {
    }

    public static void main(String[] args) throws Exception {
        Config cfg = Config.parse(args);
        InetAddress serverIp = InetAddress.getByName(cfg.host);

        try (DatagramSocket socket = new DatagramSocket()) {
            System.out.println(
                "Sending UDP datagrams to " + cfg.host + ":" + cfg.port
                    + " from seq=" + cfg.start + " count=" + cfg.count
                    + " prefix=\"" + cfg.prefix + "\" delayMs=" + cfg.delayMs
            );

            for (int i = 0; i < cfg.count; i++) {
                int seq = cfg.start + i;
                String message = cfg.prefix + seq;
                byte[] data = message.getBytes(StandardCharsets.UTF_8);
                DatagramPacket packet = new DatagramPacket(data, data.length, serverIp, cfg.port);
                socket.send(packet);

                System.out.println("sent> " + message);

                maybeWaitBetweenPackets(i, cfg.count, cfg.delayMs);
            }
        }

        System.out.println("Done.");
    }

    private static void maybeWaitBetweenPackets(int idx, int totalCount, int delayMs) throws InterruptedException {
        if (delayMs > 0 && idx < totalCount - 1) {
            Thread.sleep(delayMs);
        }
    }

    private static final class Config {
        final String host;
        final int port;
        final int start;
        final int count;
        final int delayMs;
        final String prefix;

        Config(String host, int port, int start, int count, int delayMs, String prefix) {
            this.host = host;
            this.port = port;
            this.start = start;
            this.count = count;
            this.delayMs = delayMs;
            this.prefix = prefix;
        }

        static Config parse(String[] args) {
            String host = null;
            int port = DEFAULT_PORT;
            int start = DEFAULT_START;
            int count = DEFAULT_COUNT;
            int delayMs = DEFAULT_DELAY_MS;
            String prefix = "";

            for (int i = 0; i < args.length; i++) {
                String arg = args[i];
                switch (arg) {
                    case "--host" -> host = requireValue(args, ++i, "--host");
                    case "--port" -> port = Integer.parseInt(requireValue(args, ++i, "--port"));
                    case "--start" -> start = Integer.parseInt(requireValue(args, ++i, "--start"));
                    case "--count" -> count = Integer.parseInt(requireValue(args, ++i, "--count"));
                    case "--delay-ms" -> delayMs = Integer.parseInt(requireValue(args, ++i, "--delay-ms"));
                    case "--prefix" -> prefix = requireValue(args, ++i, "--prefix");
                    case "--help", "-h" -> printUsageAndExit(0);
                    default -> {
                        System.err.println("Unknown argument: " + arg);
                        printUsageAndExit(1);
                    }
                }
            }

            if (host == null || host.isEmpty()) {
                System.err.println("Missing required argument: --host");
                printUsageAndExit(1);
            }
            if (count < 1) {
                System.err.println("--count must be >= 1");
                printUsageAndExit(1);
            }
            if (delayMs < 0) {
                System.err.println("--delay-ms must be >= 0");
                printUsageAndExit(1);
            }

            return new Config(host, port, start, count, delayMs, prefix);
        }

        private static String requireValue(String[] args, int index, String flag) {
            if (index >= args.length) {
                System.err.println("Missing value for " + flag);
                printUsageAndExit(1);
            }
            return args[index];
        }

        private static void printUsageAndExit(int code) {
            System.out.println(
                "Usage: java -cp client UdpClient --host <SERVER_IP> [--port 5001] "
                    + "[--start 1] [--count 100] [--delay-ms 10] [--prefix \"\"]"
            );
            System.exit(code);
        }
    }
}
