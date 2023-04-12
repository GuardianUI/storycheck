/**
 *
 * Mock Crypto Wallet Provider that enables e2e test automation.
 *
 * Builds on Matt's work at https://github.com/GuardianUI/PlaywrightFramework
 *
 */
import { JsonRpcProvider } from "@ethersproject/providers";
import { Wallet } from "@ethersproject/wallet";
import { MockWallet } from "./mocks/MockWallet";

// Setup an ethereum mock wallet
// in this browser context,
// unless there is already one in place
if (!window["ethereum"]) {
  const ANVIL_URL = "http://127.0.0.1:8545";

  // link to local foundry anvil fork of mainnet
  const rpcProvider = new JsonRpcProvider(ANVIL_URL);
  
  // create a new burn wallet for each test
  const signer = Wallet.createRandom();
  console.info('Created mock user wallet with address: ', signer.address)

  // emulate metamask wallet that does not require user UI interactions to confirm transactions
  // The focus is mainly on testing dapp's interaction with a live blockchain.
  // No emphasis on testing wallet UI until there is better support by wallet providers of automated testing.
  const provider = new MockWallet(signer, rpcProvider);

  window["ethereum"] = provider;

  const balance = provider.getBalance(
    signer.address,
    "latest"
  );
  console.info('User wallet balance is: ', balance)

  // Init wallet with story prerequisites
  const newBalance = "0x1000"
  console.info('Setting new balance for user wallet', signer.address, newBalance)
  provider.send("anvil_setBalance", [
                signer.address,
                // TODO: get actual initial balance from prerequisites section of story markdown
                newBalance,
  ])

  balance = provider.getBalance(
    signer.address,
    "latest"
  );
  console.info('User wallet balance is: ', balance)

} else {
  console.info('ETH mock user wallet already exist in this browser context. User account address: ', signer.address)
}
