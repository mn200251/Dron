
#include "tests.h"

int led_test() {
    const char *chipname = "gpiochip4";
    struct gpiod_chip *chip;
    struct gpiod_line *line;
    int ret;
    std::cout<<"Hello"<<std::endl;
    // Open the GPIO chip
    chip = gpiod_chip_open_by_name(chipname);
    if (!chip) {
        std::cerr << "Failed to open the GPIO chip" << std::endl;
        return 1;
    }

    // Get the GPIO line (pin 17)
    line = gpiod_chip_get_line(chip, LED_PIN);
    if (!line) {
        std::cerr << "Failed to get the GPIO line" << std::endl;
        gpiod_chip_close(chip);
        return 1;
    }

    // Request the line as output
    ret = gpiod_line_request_output(line, CONSUMER, 0);
    if (ret < 0) {
        std::cerr << "Failed to request the GPIO line as output" << std::endl;
        gpiod_chip_close(chip);
        return 1;
    }

    // Blink the LED
    for (int i = 0; i < 10; ++i) {
        gpiod_line_set_value(line, 1); // LED on
        sleep(1);
        gpiod_line_set_value(line, 0); // LED off
        sleep(1);
    }

    // Release the line and close the chip
    gpiod_line_release(line);
    gpiod_chip_close(chip);

    return 0;
}
