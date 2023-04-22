import { Provider, JsonRpcProvider } from "@ethersproject/providers";
import { Signer } from "ethers";
import { Eip1193Bridge } from "@ethersproject/experimental";
class MockInternalMetaMask {
  isUnlocked() {
    console.warn("MockInternalMetaMask.isUnlocked", { signer, provider });
    return true;
  }
}

export class MockWallet extends Eip1193Bridge {
  constructor(signer, provider) {
    super(signer, provider);
    console.debug("MockWallet constructor called") // , { signer, provider });
  }

  // Match Metamask interface
  _isMM = true

  // Match Metamask interface
  get isMetaMask() {
    console.debug("MockWallet.isMetaMask: ", this._isMM);
    return this._isMM
  }

  _metamask = new MockInternalMetaMask();




  async send(method, params) {
    console.debug("MockWallet.send START", { method, params });
    try {
      // handle backwards compatibility with deprecated methods
      if (method == 'eth_requestAccounts') {
        console.debug("MockWallet.send - mapping Metamask legacy eth_requestAccounts to ETH standard eth_accounts")
        method = 'eth_accounts'
      }
      // forward to default bridge implementation
      const result = await super.send(method, params);
      console.debug("MockWallet.send RETURNS result", { method, params, result });
      return result
    } catch (e) {
      console.error("MockWallet.send THROWS error", { method, params, e }, e.stack);
      throw e
    } finally {
      console.debug("MockWallet.send END!", { method, params });
    }
  }
}
