CC = gcc
CFLAGS = -I/usr/local/include
LDFLAGS = -L/usr/local/lib -lrp

all: laser_lock_pid

laser_lock_pid: laser_lock_pid.c
	$(CC) laser_lock_pid.c -o laser_lock_pid $(CFLAGS) $(LDFLAGS)

clean:
	rm -f laser_lock_pid
