#[ic_cdk::query]
fn greet(name: String) -> String {
    format!("Hello, {}!", name)
}

// Export Candid so candid-extractor can generate the .did
ic_cdk::export_candid!();
