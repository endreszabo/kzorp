# This is a teporaly Makefile untill autoconfigured this module

all: iptables-module-make

install: kernel-module-install python-module-install iptables-module-install

iptables-module-make:
	(cd iptables && libtoolize -f --copy)
	(cd iptables && aclocal)
	(cd iptables && autoheader)
	(cd iptables && automake --add-missing --force-missing --copy --foreign)
	(cd iptables && autoconf)
	(cd iptables && ./configure)
	(cd iptables && make)

kernel-module-install:
	install -m 0755 -d $(DESTDIR)/usr/src/kzorp-3.2
	cp -a kernel-module/* $(DESTDIR)/usr/src/kzorp-3.2

python-module-install:
	for pversion in `pyversions -vi`; do \
		(cd pylib/kzorp && python$$pversion setup.py install --prefix $(DESTDIR)/usr --install-layout=deb); \
	done;

iptables-module-install:
	(cd iptables && make install DESTDIR=$(DESTDIR))
