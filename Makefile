bitcoin-start:
	bitcoind -conf=$(CURDIR)/bitcoin.conf -datadir=$(CURDIR)/bitcoin_data --port=18444

bitcoin-mining:
	chmod +x $(CURDIR)/scripts/bitcoin.mining_block.sh
	$(CURDIR)/scripts/bitcoin.mining_block.sh $(address) $(block)

bitcoin-balance:
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf getbalance

bitcoin-newwallet:
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf -named createwallet wallet_name="nara" load_on_startup=true

bitcoin-utxo:
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf listunspent

bitcoin-newaddress:
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf getnewaddress "nara"

bitcoin-getaddress:
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf getaddressesbylabel "nara"

bitcoin-send:
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf sendtoaddress $(address) $(amount)
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf generatetoaddress 1 bcrt1qj4k3909pq4p0pfc94xpsgzl5rkkm27elfpeqa9

bitcoin-mine:
	bitcoin-cli -conf=$(CURDIR)/bitcoin.conf generatetoaddress 1 bcrt1qj4k3909pq4p0pfc94xpsgzl5rkkm27elfpeqa9