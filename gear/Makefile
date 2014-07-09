#
# Makefile
#

export CC := gcc
export AR := $(COMMAND_PREFIX)ar

#
# Global flags (used in compile and link)
#
GLOBAL_CFLAGS = -g  

#
# LINKER_OPTIONS : used during linking
# 
LINKER_OPTIONS = -lm

#
# List source files
#
SRCS=  gear.c
       
       
OBJS=${SRCS:%.c=%.o}
DST=gear

%.o:%.c
	$(CC) -c $(GLOBAL_CFLAGS) $*.c -o $*.o

${DST}:${OBJS}
	$(CC) $(GLOBAL_LDFLAGS) $(LINKER_OPTIONS) ${OBJS} -o $@

clean:
	rm ${OBJS} 
