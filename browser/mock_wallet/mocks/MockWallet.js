import { Provider, JsonRpcProvider } from "@ethersproject/providers";
import { Signer } from "ethers";
import { Eip1193Bridge } from "@ethersproject/experimental/lib/eip1193-bridge";

class MockInternalMetaMask {
  isUnlocked() {
    console.warn("MockInternalMetaMask.isUnlocked", { signer, provider });
    return true;
  }
}

export class MockWallet extends Eip1193Bridge {
  constructor(signer, provider) {
    super(signer, provider);
    console.warn("MockWallet constructor called", { signer, provider });
  }

  // Match Metamask interface
  isMetaMask = true;
  _metamask = new MockInternalMetaMask();


  async sendAsync(...args) {
    console.warn("sendAsync", { args });
    return this.send(...args);
  }

  async send(...args) {
    console.warn("MockWallet.send START", { args });
    try {
      const result = await super.send(...args);
      console.warn("MockWallet.send RETURNS result", { result });
      return result
    } catch (e) {
      console.error("MockWallet.send THROWS error", { error }, e.stack);
    } finally {
      console.warn("MockWallet.send END!");
    }
  }
}
