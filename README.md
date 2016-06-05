# bitmarket_pl utilities
Currently only python script which regulary checks what is the cut off swap rate, and updates position accordingly so your position earns as much money as possible.

Python 2.7. At the moment only one external dependency `simplejson`. You should be able to install it using `easy_install`:
```bash
easy_install simplejson
```

Before running you need to rename `config.json.example` to `config.json` and fill correctly api keys from bitmarket.pl.
