dfx identity new minter

export MINTER_ACCOUNT_ID=$(dfx ledger --identity minter account-id)
export DEFAULT_ACCOUNT_ID=$(dfx ledger --identity default account-id)

dfx deploy --specified-id ryjl3-tyaaa-aaaaa-aaaba-cai icp_ledger --argument "
  (variant {
    Init = record {
      minting_account = \"$MINTER_ACCOUNT_ID\";
      initial_values = vec {
        record {
          \"$DEFAULT_ACCOUNT_ID\";
          record {
            e8s = 10_000_000_000 : nat64;
          };
        };
      };
      send_whitelist = vec {};
      transfer_fee = opt record {
        e8s = 10_000 : nat64;
      };
      token_symbol = opt \"LICP\";
      token_name = opt \"Local ICP\";
    }
  })
"

