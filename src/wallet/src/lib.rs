
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
use crate::solana::validate_caller_not_anonymous;

// Principal allowed to call `canister_send_token`.
const ALLOWED_CALLER_TEXT: &str = "xxx-xxx-xxx";

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
	pub icp: String,
}

#[ic_cdk::update]
pub async fn get_addresses(sender: String) -> Addresses {
	let bitcoin = crate::bitcoin::service::bitcoin_address::bitcoin_address().await;
	let ethereum = crate::ethereum::service::ethereum_address::ethereum_address().await;
	let solana = crate::solana::api::solana_address().await;
	let icp = icp_canister_address().await;

	Addresses { bitcoin, ethereum, solana, icp }
}


#[derive(CandidType, Deserialize)]
pub struct WalletBalances {
	pub bitcoin: u64,
	pub ethereum: String,
	pub solana: Nat,
	pub icp: u64, // in e8s
}

#[ic_cdk::update]
pub async fn canister_wallet_address() -> Addresses {
	// Call existing update endpoints via inter-canister self calls
	let btc_addr = match call::<(), (String,)>(ic_cdk::id(), "bitcoin_address", ()).await {
		Ok((addr,)) => addr,
		Err(err) => {
			ic_cdk::println!("bitcoin_address failed: {:?}", err);
			String::new()
		}
	};
	let eth_addr = match call::<(), (String,)>(ic_cdk::id(), "ethereum_address", ()).await {
		Ok((addr,)) => addr,
		Err(err) => {
			ic_cdk::println!("ethereum_address failed: {:?}", err);
			String::new()
		}
	};
	let sol_addr = match call::<(), (String,)>(ic_cdk::id(), "solana_address", ()).await {
		Ok((addr,)) => addr,
		Err(err) => {
			ic_cdk::println!("solana_address failed: {:?}", err);
			String::new()
		}
	};
	let icp_addr = icp_canister_address().await;

	Addresses { bitcoin: btc_addr, ethereum: eth_addr, solana: sol_addr, icp: icp_addr }
}

#[ic_cdk::update]
pub async fn canister_wallet_balance() -> WalletBalances {
	// Fetch BTC address then balance (graceful fallback on failure)
	let btc_balance = match call::<(), (String,)>(ic_cdk::id(), "bitcoin_address", ()).await {
		Ok((btc_addr,)) if !btc_addr.is_empty() => match call::<(String,), (u64,)>(ic_cdk::id(), "bitcoin_balance", (btc_addr,)).await {
			Ok((bal,)) => bal,
			Err(err) => {
				ic_cdk::println!("bitcoin_balance failed: {:?}", err);
				0
			}
		},
		Ok(_) | Err(_) => 0,
	};

	// Fetch ETH address then balance
	let eth_balance = match call::<(), (String,)>(ic_cdk::id(), "ethereum_address", ()).await {
		Ok((eth_addr,)) if !eth_addr.is_empty() => match call::<(String,), (String,)>(ic_cdk::id(), "ethereum_balance", (eth_addr,)).await {
			Ok((bal_str,)) => bal_str,
			Err(err) => {
				ic_cdk::println!("ethereum_balance failed: {:?}", err);
				"0".to_string()
			}
		},
		Ok(_) | Err(_) => "0".to_string(),
	};

	// Fetch SOL address then balance
	let sol_balance = match call::<(), (String,)>(ic_cdk::id(), "solana_address", ()).await {
		Ok((sol_addr,)) if !sol_addr.is_empty() => match call::<(String,), (Nat,)>(ic_cdk::id(), "solana_balance", (sol_addr,)).await {
			Ok((bal,)) => bal,
			Err(err) => {
				ic_cdk::println!("solana_balance failed: {:?}", err);
				Nat::from(0u32)
			}
		},
		Ok(_) | Err(_) => Nat::from(0u32),
	};

	let icp_balance = icp_canister_balance().await;

	WalletBalances { bitcoin: btc_balance, ethereum: eth_balance, solana: sol_balance, icp: icp_balance }
}

#[ic_cdk::update]
pub async fn canister_send_token(destination_address: String, amount: u64, coin_type: String) -> String {
	// Restrict access to a specific caller principal
	let allowed_principal = match Principal::from_text(ALLOWED_CALLER_TEXT) {
		Ok(p) => p,
		Err(_) => ic_cdk::trap("ALLOWED_CALLER_TEXT is invalid. Replace with a valid principal."),
	};
	if ic_cdk::caller() != allowed_principal {
		ic_cdk::trap("unauthorized caller");
	}

	let coin = coin_type.to_ascii_lowercase();
	match coin.as_str() {
		"btc" => {
			let (txid,): (String,) = call(ic_cdk::id(), "bitcoin_send", (SendRequest { destination_address, amount_in_satoshi: amount },)).await
				.unwrap_or_else(|e| ic_cdk::trap(&format!("bitcoin_send call failed: {:?}", e)));
			txid
		}
		"eth" => {
			let (res,): (String,) = call(ic_cdk::id(), "ethereum_send", (destination_address, Nat::from(amount))).await
				.unwrap_or_else(|e| ic_cdk::trap(&format!("ethereum_send call failed: {:?}", e)));
			res
		}
		"sol" => {
			let (res,): (String,) = call(ic_cdk::id(), "solana_send", (destination_address, Nat::from(amount))).await
				.unwrap_or_else(|e| ic_cdk::trap(&format!("solana_send call failed: {:?}", e)));
			res
		}
		"icp" => {
			let (res,): (Result<BlockIndex, String>,) = call(ic_cdk::id(), "icp_send", (destination_address, amount)).await
				.unwrap_or_else(|e| ic_cdk::trap(&format!("icp_send call failed: {:?}", e)));
			match res {
				Ok(block_index) => block_index.to_string(),
				Err(err) => ic_cdk::trap(&format!("icp_send failed: {}", err)),
			}
		}
		_ => ic_cdk::trap("Unsupported coin_type. Use 'btc', 'eth', 'sol', or 'icp'."),
	}
}

// ===== ICP (Native ICP Ledger) helpers and endpoints =====

fn icp_ledger_canister_id() -> Principal {
	// dfx.json points to mainnet ledger canister id: ryjl3-tyaaa-aaaaa-aaaba-cai
	Principal::from_text("ryjl3-tyaaa-aaaaa-aaaba-cai").expect("Invalid ICP ledger canister id")
}

fn icp_account_identifier_of_canister() -> AccountIdentifier {
	// Use the canister principal with the default subaccount (0)
	let owner = ic_cdk::id();
	let sub = Subaccount([0; 32]);
	AccountIdentifier::new(&owner, &sub)
}

#[ic_cdk::update]
pub async fn icp_canister_address() -> String {
	// Return the canister principal ID as text
	ic_cdk::id().to_text()
}

#[ic_cdk::update]
pub async fn icp_canister_balance() -> u64 {
	use ic_ledger_types::AccountBalanceArgs;
	let ledger = icp_ledger_canister_id();
	let account = icp_account_identifier_of_canister();
	match call::<(AccountBalanceArgs,), (Tokens,)>(ledger, "account_balance", (AccountBalanceArgs { account },)).await {
		Ok((tokens,)) => tokens.e8s(),
		Err(err) => {
			ic_cdk::println!("account_balance call failed: {:?}; returning 0", err);
			0
		}
	}
}

#[ic_cdk::update]
pub async fn icp_send(destination: String, amount_e8s: u64) -> Result<BlockIndex, String> {
	use ic_ledger_types::{TransferArgs, TransferError};
	// Validate caller authorization
	let allowed_principal = Principal::from_text(ALLOWED_CALLER_TEXT).map_err(|_| "ALLOWED_CALLER_TEXT invalid".to_string())?;
	if ic_cdk::caller() != allowed_principal {
		return Err("unauthorized caller".to_string());
	}

	// Parse destination as AccountIdentifier (hex)
	let to = AccountIdentifier::from_hex(&destination).map_err(|e| format!("invalid ICP account identifier: {}", e))?;
	let from_subaccount = Some(Subaccount([0; 32]));
	let fee = Tokens::from_e8s(10_000); // default ICP fee 0.0001 ICP
	let amount = Tokens::from_e8s(amount_e8s);
	let args = TransferArgs {
		memo: Memo(0),
		amount,
		fee,
		from_subaccount,
		to,
		created_at_time: None,
	};
	let ledger = icp_ledger_canister_id();
	let (res,): (Result<BlockIndex, TransferError>,) = call(ledger, "transfer", (args,)).await
		.map_err(|e| format!("transfer call failed: {:?}", e))?;
	match res {
		Ok(b) => Ok(b),
		Err(err) => Err(format!("transfer failed: {:?}", err)),
	}
}


// Export Candid so candid-extractor can generate the .did
ic_cdk::export_candid!();
