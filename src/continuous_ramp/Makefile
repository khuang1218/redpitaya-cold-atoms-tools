CC = gcc
CFLAGS = -I/usr/local/include
LDFLAGS = -L/usr/local/lib -lrp

all: continuous_ramp

continuous_ramp: continuous_ramp.c
	$(CC) continuous_ramp.c -o continuous_ramp $(CFLAGS) $(LDFLAGS)

clean:
	rm -f continuous_ramp
