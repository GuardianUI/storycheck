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
    this._
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
    let writeTx, writeTxException, writeTxResult = undefined
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
      // handle legacy MetaMask method wallet_switchEthereumChain
      // https://eips.ethereum.org/EIPS/eip-3326
      // https://docs.metamask.io/wallet/reference/rpc-api/#wallet_switchethereumchain
      if (method == 'wallet_switchEthereumChain') {
        console.debug("MockWallet.send - ignoring Metamask legacy wallet_switchEthereumChain")
        result = null
      } else if (params && params.length && params[0].from && method === 'eth_sendTransaction') {
        writeTx = {method, params}
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
        // result = tx.hash
        result = tx
      } else {
        // All other transactions the base class works for
        result = await super.send(method, params)
      }
      console.debug("MockWallet.send RETURNS result", { method, params, result });
      writeTxResult = result
      return result
    } catch (e) {
      writeTxException = e
      console.error("MockWallet.send THROWS error", { method, params, e }, e.stack);
      throw e
    } finally {
      // log write tx in StoryCheck snapshot
      if (writeTx) {
        console.debug("MockWallet.send logging write tx");
        __guardianui__logTx({ writeTx, writeTxException, writeTxResult })
      }
      console.debug("MockWallet.send END!", { method, params });
    }
  }
}
