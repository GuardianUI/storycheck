/**
 *
 * Mock Crypto Wallet Provider that enables e2e test automation.
 *
 * Builds on Matt's work https://github.com/GuardianUI/PlaywrightFramework
 *
 */
import { JsonRpcProvider } from "@ethersproject/providers";
import { Wallet } from "@ethersproject/wallet";
import { MockWallet } from "./mocks/MockWallet";

const rpcProvider = new JsonRpcProvider("https://eth-mainnet.g.alchemy.com/v2/0Uk2xg_qksy5OMviwu8MOHMHVJX4mQ1D", 1);
const signer = Wallet.createRandom();
const provider = new MockWallet(signer, rpcProvider);

window["ethereum"] = provider;
