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


try {

  // Setup an ethereum mock wallet
  // in this browser context,
  // unless there is already one in place
  if (!window["ethereum"]) {

    await window.__guardianui_hook_rpc_router()
    console.debug('Mock RPC router hooked.')

    // const ANVIL_URL = "http://127.0.0.1:8545";

    // const chainId = '__GUARDIANUI_MOCK__CHAIN_ID'
    // link to local foundry anvil fork of mainnet
    const rpcUrl = '__GUARDIANUI_MOCK__RPC'
    const rpcProvider = await new JsonRpcProvider(rpcUrl) // , chainId) // , {chainId: 5});
    console.debug('JsonRpcProvider waiting to become ready')
    const isRpcReady = await rpcProvider.ready
    console.info('JsonRpcProvider ready: ', { isRpcReady, rpcUrl })
    // create a new burn wallet for each test

    const pkey = '__GUARDIANUI_MOCK__PRIVATE_KEY'
    console.debug('mock wallet private key: ', { pkey })
    const signer = await new Wallet(pkey, rpcProvider);
    console.info('Created mock user wallet with address: ', signer.address)

    // emulate metamask wallet that does not require user UI interactions to confirm transactions
    // The focus is mainly on testing dapp's interaction with a live blockchain.
    // No emphasis on testing wallet UI until there is better support by wallet providers of automated testing.
    const wallet = new MockWallet(signer, rpcProvider);

    window["ethereum"] = wallet;

    let balance = await wallet.send("eth_getBalance", [
      signer.address,
      "latest"
    ]);
    console.debug('User wallet balance is: ', { balance })

    const isInitialized = window.localStorage.getItem('__GUARDIANUI_MOCK__IS_INITIALIZED')
    if (isInitialized) {
      console.debug('User mock wallet already initialized.')
    } else {
      console.debug('Initializing user mock wallet...')
      // Init wallet with story prerequisites
      // default balance: 10,000 ETH (same as anvil defaults)
      const ethAmount = "10000"
      const newBalance = await ethers.utils.parseEther(ethAmount).toHexString()
      console.debug('Setting new balance for user wallet', signer.address, newBalance)
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
      console.debug('User mock wallet initialized.')
      window.localStorage.setItem('__GUARDIANUI_MOCK__IS_INITIALIZED', true)

    }
  } else {
    console.info('ETH mock user wallet already exist in this browser context. User account address: ', signer.address)
  }
} catch (e) {
  console.error('Error while setting up window.ethereum mock wallet', e)
}
