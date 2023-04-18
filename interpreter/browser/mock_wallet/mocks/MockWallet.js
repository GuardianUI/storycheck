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
  _isConnected = false

  constructor(signer, provider) {
    super(signer, provider);
    this._isConnected = true
    console.info("MockWallet created") // , { signer, provider });
  }

  // Match Metamask interface
  isMetaMask = true;
  _metamask = new MockInternalMetaMask();

  isConnected() {
    return this._isConnected
  }

  // async request(...args) {
  //   console.debug("MockWallet.request", { args });
  //       return await this.send(...args);
  // }

  async sendAsync(...args) {
    console.debug("MockWallet.sendAsync", { args });
    return this.send(...args);
  }

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
