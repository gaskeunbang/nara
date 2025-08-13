use crate::bitcoin::BTC_CONTEXT;
use ic_cdk::{
    api::management_canister::bitcoin::{bitcoin_get_balance, GetBalanceRequest},
    update,
};

/// Returns the balance of the given bitcoin address.
#[update]
pub async fn bitcoin_balance(address: String) -> u64 {
    let ctx = BTC_CONTEXT.with(|ctx| ctx.get());

    let (balance,) = bitcoin_get_balance(GetBalanceRequest {
        address,
        network: ctx.network,
        min_confirmations: None,
    })
    .await
    .unwrap();

    balance
}
