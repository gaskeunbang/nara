use alloy::signers::{icp::IcpSigner, Signer};

use crate::ethereum::{create_derivation_path_from_sender, get_ecdsa_key_name};

#[ic_cdk::update]
pub async fn ethereum_address(sender: String) -> Result<String, String> {
	// Setup signer
	let ecdsa_key_name = get_ecdsa_key_name();
	let derivation_path = create_derivation_path_from_sender(&sender);
	let signer = IcpSigner::new(derivation_path, &ecdsa_key_name, None)
		.await
		.map_err(|e| e.to_string())?;

	let address = signer.address();
	Ok(address.to_string())
}