import { JsonRpcProvider } from "@ethersproject/providers";
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
      // workaround for a known issue with ethers
      // https://github.com/ethers-io/ethers.js/issues/1683
            // If from is present on eth_call it errors, removing it makes the library set
      // from as the connected wallet which works fine
      if (params && params.length && params[0].from && method === 'eth_call') delete params[0].from
      let result
      // For sending a transaction if we call send it will error
      // as it wants gasLimit in sendTransaction but hexlify sets the property gas
      // to gasLimit which makes sensd transaction error.
      // This have taken the code from the super method for sendTransaction and altered
      // it slightly to make it work with the gas limit issues.
      if (params && params.length && params[0].from && method === 'eth_sendTransaction') {
        // Hexlify will not take gas, must be gasLimit, set this property to be gasLimit
        params[0].gasLimit = params[0].gas
        delete params[0].gas
        // If from is present on eth_sendTransaction it errors, removing it makes the library set
        // from as the connected wallet which works fine
        delete params[0].from
        const req = JsonRpcProvider.hexlifyTransaction(params[0])
        // Hexlify sets the gasLimit property to be gas again and send transaction requires gasLimit
        req.gasLimit = req.gas
        delete req.gas
        // Send the transaction
        const tx = await this.signer.sendTransaction(req)
        result = tx.hash
      } else {
        // All other transactions the base class works for
        result = await super.send(method, params)
      }
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
