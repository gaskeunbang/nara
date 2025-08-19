
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
use ic_ledger_types::{BlockIndex, Memo, Tokens};
use ic_ledger_types::AccountIdentifier;
use serde_json::Value;
use ic_cdk::api::call::call;
use candid::Principal;
use ic_ledger_types::Subaccount;
use ic_cdk::update;

fn ledger_canister_id() -> Principal {
	// Try to read from canister_ids.json embedded at compile-time (local or ic)
	const CANISTER_IDS_JSON: &str = include_str!("../../../canister_ids.json");
	if let Ok(v) = serde_json::from_str::<Value>(CANISTER_IDS_JSON) {
		if let Some(obj) = v.get("icp_ledger_canister") {
			if let Some(local_id) = obj.get("local").and_then(|s| s.as_str()) {
				if let Ok(p) = Principal::from_text(local_id) { return p; }
			}
			if let Some(ic_id) = obj.get("ic").and_then(|s| s.as_str()) {
				if let Ok(p) = Principal::from_text(ic_id) { return p; }
			}
		}
	}
	// Fallback to mainnet ICP ledger canister id
	Principal::from_text("ryjl3-tyaaa-aaaaa-aaaba-cai").expect("valid mainnet ledger id")
}

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
	let bitcoin = crate::bitcoin::service::bitcoin_address::bitcoin_address().await;
	let ethereum = crate::ethereum::service::ethereum_address::ethereum_address().await;
	let solana = crate::solana::api::solana_address().await;

	Addresses { bitcoin, ethereum, solana }
}

// ICP
#[ic_cdk::update]
pub async fn icp_send(to_principal: Principal, amount: Tokens) -> Result<BlockIndex, String> {
	let to_subaccount = Subaccount([0; 32]);
	let transfer_args = ic_ledger_types::TransferArgs {
			memo: Memo(0),
			amount: amount,
			fee: Tokens::from_e8s(10_000),
			// The subaccount of the account identifier that will be used to withdraw tokens and send them
			// to another account identifier. If set to None then the default subaccount will be used.
			// See the [Ledger doc](https://internetcomputer.org/docs/current/developer-docs/integrations/ledger/#accounts).
			from_subaccount: None,
			to: AccountIdentifier::new(&to_principal, &to_subaccount),
			created_at_time: None,
	};
	ic_ledger_types::transfer(ledger_canister_id(), transfer_args)
			.await
			.map_err(|e| format!("failed to call ledger: {:?}", e))?
			.map_err(|e| format!("ledger transfer error {:?}", e))
}

#[ic_cdk::update]
pub async fn icp_balance() -> Nat {
	// Compute this canister's default account identifier
	let sub = Subaccount([0; 32]);
	let account = AccountIdentifier::new(&ic_cdk::api::id(), &sub);
	let args = ic_ledger_types::AccountBalanceArgs { account };
	let result: Result<(Tokens,), _> = call(ledger_canister_id(), "account_balance", (args,)).await;
	match result {
		Ok((tokens,)) => Nat::from(tokens.e8s()),
		Err(_) => Nat::from(0u64),
	}
}

#[ic_cdk::update]
pub async fn icp_address() -> String {
	ic_cdk::api::id().to_string()
}

// Export Candid so candid-extractor can generate the .did
ic_cdk::export_candid!();
