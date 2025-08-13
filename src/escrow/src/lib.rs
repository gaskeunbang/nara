
#[path = "bitcoin/lib.rs"]
pub mod bitcoin;

use ic_cdk::bitcoin_canister::{GetUtxosResponse, MillisatoshiPerByte, Network};
use crate::bitcoin::SendRequest;

// Export Candid so candid-extractor can generate the .did
ic_cdk::export_candid!();
