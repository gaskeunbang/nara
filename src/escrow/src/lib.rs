
#[path = "bitcoin/lib.rs"]
pub mod bitcoin;
#[path = "ethereum/lib.rs"]
pub mod ethereum;

use ic_cdk::api::management_canister::bitcoin::{BitcoinNetwork, GetUtxosResponse, MillisatoshiPerByte};
use crate::bitcoin::SendRequest;
use candid::Nat;

// Export Candid so candid-extractor can generate the .did
ic_cdk::export_candid!();
