// File: interpreter/browser/mock_wallet/mocks/MockWallet.js
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
    this._events = {};  // Initialize event system
    this._isMM = true;  // Set internal flag for isMetaMask getter
    console.debug("MockWallet constructor called") // , { signer, provider });
    // Emulate basic events
    this.on = (event, cb) => {
      if (!this._events[event]) this._events[event] = [];
      this._events[event].push(cb);
    };
    this.emit = (event, ...args) => {
      console.debug(`Emitting event: ${event}`, args);
      if (this._events[event]) this._events[event].forEach(cb => cb(...args));
    };
    // Emit 'connect' to simulate detection
    setTimeout(() => this.emit('connect', { chainId: this.chainId }), 100);
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
        // Return array with signer address to simulate connected account
        return [this.signer.address];
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
        // Handle EIP-1559 (type 0x2) explicitly
        if (params[0].type === '0x2' || params[0].type === 2) {
          params[0].type = 2; // Ensure integer type
          params[0].chainId = parseInt(await this.send('eth_chainId', []), 16); // Add chainId for signing
        }        
        const req = JsonRpcProvider.hexlifyTransaction(params[0])
        // Hexlify sets the gasLimit property to be gas again and send transaction requires gasLimit
        req.gasLimit = req.gas
        delete req.gas
        // Fix: hexlify makes chainId a hex string, but signer expects number
        if (req.chainId) req.chainId = parseInt(req.chainId, 16);        
        // Fix: hexlify makes type a hex string, but signer expects number
        if (req.type) req.type = parseInt(req.type, 16);        
        // Send the transaction
        const tx = await this.signer.sendTransaction(req)
        // result = tx.hash
        // result = tx
        result = tx.hash || ethers.utils.keccak256(await tx.serialize()); // Return hash, simulate if needed
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