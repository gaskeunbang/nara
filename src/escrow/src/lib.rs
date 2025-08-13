
#[path = "bitcoin/lib.rs"]
pub mod bitcoin;
#[path = "ethereum/lib.rs"]
pub mod ethereum;
#[path = "solana/lib.rs"]
pub mod solana;

use ic_cdk::api::management_canister::bitcoin::{BitcoinNetwork, GetUtxosResponse, MillisatoshiPerByte};
use crate::bitcoin::SendRequest;
use candid::Nat;

#[ic_cdk::init]
pub fn init(bitcoin_network: BitcoinNetwork, solana_init: Option<solana::InitArg>) {
	bitcoin::bitcoin_init(bitcoin_network);
	if let Some(arg) = solana_init {
		solana::solana_init(arg);
	}
}

#[ic_cdk::post_upgrade]
fn post_upgrade(bitcoin_network: BitcoinNetwork, solana_init: Option<solana::InitArg>) {
	bitcoin::bitcoin_post_upgrade(bitcoin_network);
	if let Some(arg) = solana_init {
		solana::solana_post_upgrade(Some(arg));
	}
}

// Export Candid so candid-extractor can generate the .did
ic_cdk::export_candid!();
