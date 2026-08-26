.POSIX:
.SUFFIXES:

all: public

.PHONY: public
public:
	hugo --destination public
	touch public/.nojekyll

.PHONY: run
run:
	hugo server --bind 127.0.0.1 --baseURL http://localhost:1313/ --port 1313

.PHONY: clean
clean:
	rm -rf public resources
