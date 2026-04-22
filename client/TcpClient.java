import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

/**
 * TCP client for the lab server protocol:
 * - UTF-8 encoding
 * - one message per line (LF)
 * - server replies with one line per request
 *
 * Usage:
 *   javac client/TcpClient.java
 *   java -cp client TcpClient --host <SERVER_IP> --port 5000
 *   java -cp client TcpClient --host <SERVER_IP> --port 5000 --message "hello"
 */
public final class TcpClient {
    private static final int DEFAULT_PORT = 5000;
    private static volatile boolean running = true;

    private TcpClient() {
    }

    public static void main(String[] args) throws Exception {
        Config cfg = Config.parse(args);

        try (Socket socket = new Socket(cfg.host, cfg.port);
             BufferedReader socketIn = new BufferedReader(
                 new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
             BufferedWriter socketOut = new BufferedWriter(
                 new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8));
             BufferedReader consoleIn = new BufferedReader(
                 new InputStreamReader(System.in, StandardCharsets.UTF_8))) {

            System.out.println("Connected to " + cfg.host + ":" + cfg.port);

            if (cfg.message != null) {
                sendLine(cfg.message, socketOut);
                String response = socketIn.readLine();
                if (response == null) {
                    System.out.println("Server closed the connection.");
                    return;
                }
                System.out.println("server> " + response);
                return;
            }

            Thread receiver = startReceiver(socketIn);
            System.out.println("Type messages and press Enter (Ctrl+Z then Enter to quit):");
            String line;
            while (running && (line = consoleIn.readLine()) != null) {
                sendLine(line, socketOut);
            }
            running = false;
            try {
                receiver.join(300);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    private static Thread startReceiver(BufferedReader socketIn) {
        Thread receiver = new Thread(() -> {
            try {
                String response;
                while (running && (response = socketIn.readLine()) != null) {
                    System.out.println("server> " + response);
                }
                if (running) {
                    System.out.println("Server closed the connection.");
                }
            } catch (IOException e) {
                if (running) {
                    System.out.println("Receive error: " + e.getMessage());
                }
            }
            running = false;
        });
        receiver.setDaemon(true);
        receiver.start();
        return receiver;
    }

    private static void sendLine(
        String line,
        BufferedWriter socketOut
    ) throws Exception {
        socketOut.write(line);
        socketOut.write('\n');
        socketOut.flush();
    }

    private static final class Config {
        final String host;
        final int port;
        final String message;

        Config(String host, int port, String message) {
            this.host = host;
            this.port = port;
            this.message = message;
        }

        static Config parse(String[] args) {
            String host = null;
            int port = DEFAULT_PORT;
            String message = null;

            for (int i = 0; i < args.length; i++) {
                String arg = args[i];
                switch (arg) {
                    case "--host" -> {
                        host = requireValue(args, ++i, "--host");
                    }
                    case "--port" -> {
                        port = Integer.parseInt(requireValue(args, ++i, "--port"));
                    }
                    case "--message" -> {
                        message = requireValue(args, ++i, "--message");
                    }
                    case "--help", "-h" -> {
                        printUsageAndExit(0);
                    }
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

            return new Config(host, port, message);
        }

        private static String requireValue(String[] args, int index, String flag) {
            if (index >= args.length) {
                System.err.println("Missing value for " + flag);
                printUsageAndExit(1);
            }
            return args[index];
        }

        private static void printUsageAndExit(int code) {
            System.out.println("Usage: java -cp client TcpClient --host <SERVER_IP> [--port 5000] [--message \"text\"]");
            System.exit(code);
        }
    }
}
