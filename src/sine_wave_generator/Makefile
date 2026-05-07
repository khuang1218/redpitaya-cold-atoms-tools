CC = gcc
CFLAGS = -I/usr/local/include -Wall -Wextra
LDFLAGS = -L/usr/local/lib -lrp

all: sine_wave_generator

sine_wave_generator: sine_wave_generator.c
	$(CC) sine_wave_generator.c -o sine_wave_generator $(CFLAGS) $(LDFLAGS)

clean:
	rm -f sine_wave_generator
