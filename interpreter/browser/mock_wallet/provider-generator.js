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
import { ethers } from "ethers"

async function setupWallet() {
  // Setup an ethereum mock wallet
  // in this browser context,
  // unless there is already one in place

  const wallet = window["ethereum"];
  if (!wallet) {
    const ANVIL_URL = "http://127.0.0.1:8545";

    // link to local foundry anvil fork of mainnet
    const rpcProvider = new JsonRpcProvider(ANVIL_URL) // , {chainId: 5});
    console.info('JsonRpcProvider waiting to become ready')
    const isRpcReady = await rpcProvider.ready
    console.info('JsonRpcProvider readiness: ', { isRpcReady })
    // console.info('JsonRpcProvider detecting chain id at: ', { ANVIL_URL })
    // network = await rpcProvider.getNetwork()
    // console.info('JsonRpcProvider detected network chain id: ', { ANVIL_URL, network })

    const pkey = '__MOCK__PRIVATE_KEY'
    console.info('mock wallet private key: ', { pkey })
    const signer = new Wallet(pkey, rpcProvider);
    console.info('Created mock user wallet with address: ', signer.address)
    console.debug("Signer connected to Provider so it can use it for blockchain methods such as signer.getBalance().");

    // emulate metamask wallet that does not require user UI interactions to confirm transactions
    // The focus is mainly on testing dapp's interaction with a live blockchain.
    // No emphasis on testing wallet UI until there is better support by wallet providers of automated testing.
    const wallet = new MockWallet(signer, rpcProvider);

    // // set the provider to use the mock wallet
    rpcProvider.getSigner = () => wallet
    console.info("Provider set to use mock wallet as a signer.");


    let balance = await wallet.send("eth_getBalance", [
      signer.address,
      "latest"
    ]);
    console.info('User wallet balance is: ', { balance })

    // Init wallet with story prerequisites
    // default balance: 10,000 ETH (same as anvil defaults)
    const ethAmount = "10000"
    const newBalance = ethers.utils.parseEther(ethAmount).toHexString()
    console.info('Setting new balance for user wallet', signer.address, newBalance)
    await wallet.send("anvil_setBalance", [
      signer.address,
      // TODO: get actual initial balance from prerequisites section of story markdown
      newBalance,
    ])
    balance = await wallet.send("eth_getBalance", [
      signer.address,
      "latest"
    ]);
    console.info('User wallet updated balance is: ', { balance })
  } else {
    console.info('ETH mock user wallet already exist in this browser context. User account address: ', signer.address)
  }
  return wallet
}

const wallet = setupWallet().
  then(wallet => {
    // Wallet setup looks good
    // We can make it available in the browser context
    window["ethereum"] = wallet;
    console.info('Mock wallet set as window.ethereum in browser context')
  }).catch (e =>
    console.error('Error while creating mock wallet.', e, e.stack)
  )
