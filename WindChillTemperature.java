import java.util.Scanner;

public class WindChillTemperature {
    private static final double MIN_TEMP = -58.0;
    private static final double MAX_TEMP = 41.0;
    private static final double MIN_WIND = 2.0;

    public static void main(String[] args) {
        try (Scanner input = new Scanner(System.in)) {
            Double temp = readDouble(input, "Enter the temperature:");
            if (temp == null) {
                return;
            }

            if (!isTempInRange(temp)) {
                System.out.printf("The temperature must be between %.0f and %.0f, inclusive%n", MIN_TEMP, MAX_TEMP);
                return;
            }

            Double wind = readDouble(input, "Enter the wind speed:");
            if (wind == null) {
                return;
            }

            if (wind < MIN_WIND) {
                System.out.printf("The wind speed must be >= %.0f%n", MIN_WIND);
                return;
            }

            double windFactor = Math.pow(wind, 0.16);
            double twc = 35.74
                + 0.6215 * temp
                - 35.75 * windFactor
                + 0.4275 * temp * windFactor;
            System.out.printf("The wind chill index is %.3f%n", twc);
        }
    }

    private static Double readDouble(Scanner input, String prompt) {
        System.out.println(prompt);
        if (input.hasNextDouble()) {
            return input.nextDouble();
        }
        System.out.println("Invalid input: Please enter a number.");
        return null;
    }

    private static boolean isTempInRange(double temp) {
        return temp >= MIN_TEMP && temp <= MAX_TEMP;
    }
}
