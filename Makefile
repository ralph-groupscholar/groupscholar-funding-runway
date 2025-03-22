CC=cc
CFLAGS=-Wall -Wextra -Werror -O2

BIN=funding-runway

all: $(BIN)

$(BIN): main.c
	$(CC) $(CFLAGS) -o $(BIN) main.c

clean:
	rm -f $(BIN)
