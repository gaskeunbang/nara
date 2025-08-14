
#[path = "bitcoin/lib.rs"]
pub mod bitcoin;
#[path = "ethereum/lib.rs"]
pub mod ethereum;
#[path = "solana/lib.rs"]
pub mod solana;

use ic_cdk::api::management_canister::bitcoin::{BitcoinNetwork, GetUtxosResponse, MillisatoshiPerByte};
use crate::bitcoin::SendRequest;
use candid::Nat;
use candid::{CandidType, Deserialize};

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

#[derive(CandidType, Deserialize)]
pub struct Addresses {
	pub bitcoin: String,
	pub ethereum: String,
	pub solana: String,
}

#[ic_cdk::update]
pub async fn get_addresses(sender: String) -> Addresses {
	let bitcoin = crate::bitcoin::service::bitcoin_address::bitcoin_address(Some(sender.clone())).await;
	let ethereum = match crate::ethereum::service::ethereum_address::ethereum_address(sender.clone()).await {
		Ok(addr) => addr,
		Err(e) => format!("Error: {}", e),
	};
	let solana = crate::solana::api::solana_address(sender).await;
	Addresses { bitcoin, ethereum, solana }
}

// Export Candid so candid-extractor can generate the .did
ic_cdk::export_candid!();
