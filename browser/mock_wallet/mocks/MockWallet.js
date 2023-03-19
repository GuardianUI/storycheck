import { Provider, JsonRpcProvider } from "@ethersproject/providers";
import { Signer } from "ethers";
import { Eip1193Bridge } from "@ethersproject/experimental/lib/eip1193-bridge";

class MockInternalMetaMask {
  isUnlocked() {
    return true;
  }
}

export class MockWallet extends Eip1193Bridge {
  constructor(signer, provider) {
    super(signer, provider);
    console.debug("Constructor called", { signer, provider });
  }

  // Match Metamask interface
  isMetaMask = true;
  _metamask = new MockInternalMetaMask();

  // Emit transaction target contract to the console
  emitTx(target, data) {
    const targetStringified = target.toString();
    const dataStringified = data.toString();

    let approvalTarget;

    if (dataStringified.substring(0, 10).toLowerCase() === "0x095ea7b3") {
      approvalTarget = "0x" + dataStringified.substring(34, 74);
    }

    console.log({ targetStringified, dataStringified, approvalTarget });
  }

  async sendAsync(...args) {
    return this.send(...args);
  }

  async send(...args) {
    const isCallbackForm =
      typeof args[0] === "object" && typeof args[1] === "function";

    let callback;
    let method;
    let params;

    if (isCallbackForm) {
      callback = args[1];
      method = args[0].method;
      params = args[0].params;
    } else {
      method = args[0];
      params = args[1];
    }

    const mockUserAccount = await this.signer.getAddress();

    // Get wallet address
    if (method === "eth_requestAccounts" || method === "eth_accounts") {
      if (isCallbackForm) {
        return callback({
          result: [mockUserAccount],
        });
      }

      return Promise.resolve(mockUserAccount);
    }

    // Get currently connected chain ID
    if (method === "eth_chainId") {
      if (isCallbackForm) {
        return callback(null, { result: "0x1" });
      }
      return Promise.resolve("0x1");
    }

    // Handle signatures, reads, and writes
    try {
      let result = null;

      if (method === "personal_sign") {
        result = await super.send("eth_sign", [params[1], params[0]]);
      } else if (
        params &&
        params.length &&
        params[0].from &&
        (method === "eth_sendTransaction" ||
          method === "eth_call" ||
          method === "eth_estimateGas")
      ) {
        console.log("send transaction");

        if (!this.signer) throw new Error("No signer");

        // Hexlify will not take gas, must be gasLimit, set this property to be gasLimit
        params[0].gasLimit = params[0].gas;
        delete params[0].gas;

        // If from is present on eth_sendTransaction it errors, removing it makes the library set
        // from as the connected wallet which works fine
        delete params[0].from;
        const req = JsonRpcProvider.hexlifyTransaction(params[0]);

        // Hexlify sets the gasLimit property to be gas again and send transaction requires gasLimit
        req["gasLimit"] = req["gas"];
        delete req["gas"];

        // Send the transaction
        if (method === "eth_sendTransaction" || method === "eth_estimateGas") {
          this.emitTx(req["to"], req["data"]);
          // We intentionally do not submit this transaction to the chain so as to not light money (or fake money) on fire
        } else {
          const tx = await this.signer.call(req);
          result = tx;
        }
      } else {
        result = await super.send(method, params);
      }
      if (isCallbackForm) return callback(null, { result });
      return result;
    } catch (error) {
      if (isCallbackForm) {
        return callback(error, null);
      }
      throw error;
    }
  }
}
