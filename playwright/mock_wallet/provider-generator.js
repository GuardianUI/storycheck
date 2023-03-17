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

WAGMI_URL =  'http://127.0.0.1:8545'

// link to local foundry anvil fork of mainnet
const rpcProvider = new JsonRpcProvider(WAGMI_URL, 1);

// create a new burn wallet for each test
const signer = Wallet.createRandom();

// emulate metamask wallet that does not require user UI interactions to confirm transactions
// The focus is mainly on testing dapp's interaction with a live blockchain.
// No emphasis on testing wallet UI until there is better support by wallet providers of automated testing.
const provider = new MockWallet(signer, rpcProvider);

window["ethereum"] = provider;
