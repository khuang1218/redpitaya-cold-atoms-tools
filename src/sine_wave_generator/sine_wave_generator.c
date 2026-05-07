/* Red Pitaya sine wave generator
 *
 * Generates a continuous sine wave on one fast analog output channel.
 */

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "redpitaya/rp.h"

static volatile sig_atomic_t keep_running = 1;

static void handle_signal(int signal)
{
    (void)signal;
    keep_running = 0;
}

static void print_usage(const char *program)
{
    printf("Usage:\n");
    printf("  %s <frequency_hz> [amplitude_v] [offset_v] [channel] [duration_s]\n\n", program);
    printf("Arguments:\n");
    printf("  frequency_hz   Sine frequency in Hz, must be > 0\n");
    printf("  amplitude_v    Peak amplitude in V, 0 to 1, default 0.5\n");
    printf("  offset_v       DC offset in V, -1 to 1, default 0.0\n");
    printf("  channel        Output channel: 1 or 2, default 1\n");
    printf("  duration_s     Run time in seconds. 0 means run until Ctrl+C, default 0\n\n");
    printf("Examples:\n");
    printf("  %s 1000\n", program);
    printf("  %s 7000 0.4 0.0 1\n", program);
    printf("  %s 100000 0.2 0.1 2 10\n", program);
}

static int validate_output_range(float amplitude, float offset)
{
    if (amplitude < 0.0f || amplitude > 1.0f) {
        fprintf(stderr, "Amplitude must be in the range 0 to 1 V.\n");
        return 0;
    }

    if (offset < -1.0f || offset > 1.0f) {
        fprintf(stderr, "Offset must be in the range -1 to 1 V.\n");
        return 0;
    }

    if ((offset + amplitude) > 1.0f || (offset - amplitude) < -1.0f) {
        fprintf(stderr, "Output would exceed the fast-output range of about +/-1 V.\n");
        fprintf(stderr, "Use a smaller amplitude or offset.\n");
        return 0;
    }

    return 1;
}

int main(int argc, char **argv)
{
    float frequency = 0.0f;
    float amplitude = 0.5f;
    float offset = 0.0f;
    int channel_number = 1;
    float duration = 0.0f;
    rp_channel_t channel = RP_CH_1;

    if (argc < 2 || argc > 6) {
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }

    frequency = atof(argv[1]);
    if (argc > 2) {
        amplitude = atof(argv[2]);
    }
    if (argc > 3) {
        offset = atof(argv[3]);
    }
    if (argc > 4) {
        channel_number = atoi(argv[4]);
    }
    if (argc > 5) {
        duration = atof(argv[5]);
    }

    if (frequency <= 0.0f) {
        fprintf(stderr, "Frequency must be greater than 0 Hz.\n");
        return EXIT_FAILURE;
    }

    if (!validate_output_range(amplitude, offset)) {
        return EXIT_FAILURE;
    }

    if (channel_number == 1) {
        channel = RP_CH_1;
    } else if (channel_number == 2) {
        channel = RP_CH_2;
    } else {
        fprintf(stderr, "Channel must be 1 or 2.\n");
        return EXIT_FAILURE;
    }

    if (duration < 0.0f) {
        fprintf(stderr, "Duration must be >= 0 seconds.\n");
        return EXIT_FAILURE;
    }

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    if (rp_Init() != RP_OK) {
        fprintf(stderr, "Red Pitaya API initialization failed.\n");
        return EXIT_FAILURE;
    }

    rp_GenReset();
    rp_GenWaveform(channel, RP_WAVEFORM_SINE);
    rp_GenFreq(channel, frequency);
    rp_GenAmp(channel, amplitude);
    rp_GenOffset(channel, offset);
    rp_GenOutEnable(channel);

    printf("Generating sine wave on OUT%d: frequency=%g Hz, amplitude=%g V, offset=%g V\n",
           channel_number, frequency, amplitude, offset);

    if (duration > 0.0f) {
        usleep((useconds_t)(duration * 1000000.0f));
    } else {
        printf("Press Ctrl+C to stop.\n");
        while (keep_running) {
            sleep(1);
        }
    }

    rp_GenOutDisable(channel);
    rp_Release();

    printf("Output stopped.\n");
    return EXIT_SUCCESS;
}
