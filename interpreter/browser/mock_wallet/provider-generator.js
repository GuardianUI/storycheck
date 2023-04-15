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
import { logger } from "ethers";

function setupWallet() {
  // Setup an ethereum mock wallet
  // in this browser context,
  // unless there is already one in place

  const wallet = window["ethereum"];
  if (!wallet) {
    const ANVIL_URL = "http://127.0.0.1:8545";

    // link to local foundry anvil fork of mainnet
    const rpcProvider = new JsonRpcProvider(ANVIL_URL);

    // create a new burn wallet for each story check
    // console.info('window.__mockMnemonic: ', window.__mockMnemonic)
    // const mnemonic = window.__mockMnemonic()

    const pkey = '__MOCK__PRIVATE_KEY'
    console.info('mock wallet private key: ', { pkey })
    const signer = new Wallet(pkey, rpcProvider);
    console.info('Created mock user wallet with address: ', signer.address)
    // signer = walletMnemonic.connect(provider)
    console.debug("Signer connected to Provider so it can use it for blockchain methods such as signer.getBalance().");

    // set the provider to use the mock wallet
    rpcProvider.getSigner = () => signer
    console.info("Provider set to use mock wallet as a signer.");

    // emulate metamask wallet that does not require user UI interactions to confirm transactions
    // The focus is mainly on testing dapp's interaction with a live blockchain.
    // No emphasis on testing wallet UI until there is better support by wallet providers of automated testing.
    const wallet = new MockWallet(signer, rpcProvider);

    window["ethereum"] = wallet;

    let balance = wallet.send("eth_getBalance", [
      signer.address,
      "latest"
    ]);
    console.info('User wallet balance is: ', { balance })

    // Init wallet with story prerequisites
    const newBalance = "0x1000"
    console.info('Setting new balance for user wallet', signer.address, newBalance)
    wallet.send("anvil_setBalance", [
      signer.address,
      // TODO: get actual initial balance from prerequisites section of story markdown
      newBalance,
    ])
  } else {
    console.info('ETH mock user wallet already exist in this browser context. User account address: ', signer.address)
  }
  return wallet
}

try {
  const wallet = setupWallet()
  let balance = wallet.send("eth_getBalance", [
    signer.address,
    "latest"
  ]);
  console.info('User wallet balance is: ', { balance })
} catch (e) {
  console.error(e => console.error('Error while creating mock wallet', e, e.stack))
}
