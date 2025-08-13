use candid::Nat;
use num::ToPrimitive;
use solana_pubkey::Pubkey;
use std::str::FromStr;

use super::{client, solana_wallet::SolanaWallet};

#[ic_cdk::update]
pub async fn solana_address() -> String {
	let owner = ic_cdk::id();
	let wallet = SolanaWallet::new(owner).await;
	wallet.solana_account().to_string()
}

#[ic_cdk::update]
pub async fn solana_balance(account: Option<String>) -> Nat {
	let account = match account {
		Some(a) => a,
		None => {
			let owner = ic_cdk::id();
			let wallet = SolanaWallet::new(owner).await;
			wallet.solana_account().to_string()
		}
	};
	let public_key = Pubkey::from_str(&account).unwrap();
	let balance = client()
		.get_balance(public_key)
		.send()
		.await
		.expect_consistent()
		.expect("Call to `getBalance` failed");
	Nat::from(balance)
}

#[ic_cdk::update]
pub async fn solana_send(to: String, amount: Nat) -> String {
	use solana_system_interface::instruction;
	use solana_message::Message;
	use solana_transaction::Transaction;

	let client = client();

	let owner = ic_cdk::id();
	let wallet = SolanaWallet::new(owner).await;

	let recipient = Pubkey::from_str(&to).unwrap();
	let payer = wallet.solana_account();
	let amount = amount.0.to_u64().unwrap();

	let instruction = instruction::transfer(payer.as_ref(), &recipient, amount);
	let message = Message::new_with_blockhash(
		&[instruction],
		Some(payer.as_ref()),
		&client.estimate_recent_blockhash().send().await.unwrap(),
	);
	let signatures = vec![payer.sign_message(&message).await];
	let transaction = Transaction { message, signatures };

	client
		.send_transaction(transaction)
		.send()
		.await
		.expect_consistent()
		.expect("Call to `sendTransaction` failed")
		.to_string()
} 