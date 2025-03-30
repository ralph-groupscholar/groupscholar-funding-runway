CC=cc
CFLAGS=-Wall -Wextra -Werror -O2
LDFLAGS=-lm

BIN=funding-runway

all: $(BIN)

$(BIN): main.c
	$(CC) $(CFLAGS) -o $(BIN) main.c $(LDFLAGS)

clean:
	rm -f $(BIN)
