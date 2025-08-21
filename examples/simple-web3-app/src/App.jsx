// examples/simple-web3-app/src/App.jsx
import { useState, useEffect } from 'react'
import { BaseError, useAccount, useConnect, useSendTransaction, useChainId, useChains, useSwitchChain } from 'wagmi'
import { parseEther } from 'viem'
import { usePublicClient } from 'wagmi'
import { normalize } from 'viem/ens'
import { mainnet } from 'viem/chains'
import { useWaitForTransactionReceipt } from 'wagmi'

export default function App() {
  const { isConnected } = useAccount()
  const { connect, connectors } = useConnect()
  const { address } = useAccount()
  const { data: hash, isPending, sendTransactionAsync, error} = useSendTransaction()
  const { isLoading: isConfirming, isSuccess: isConfirmed } =
    useWaitForTransactionReceipt({
      hash,
    })

  const chainId = useChainId()
  const [hasInitialSwitch, setHasInitialSwitch] = useState(false)
  const chains = useChains()
  const { switchChain } = useSwitchChain()
  const currentChain = chains.find(c => c.id === chainId) || mainnet
  const [to, setTo] = useState('')
  const [amount, setAmount] = useState('')
  const client = usePublicClient({ chainId: mainnet.id })
  const [rejectionError, setRejectionError] = useState(null)
  const explorerMap = { 1: 'eth', 11155111: 'sepolia', // Add more as needed
  }
  const chainSlug = explorerMap[chainId] || 'eth'

  const clearMessages = () => { setRejectionError(null); }

  const handleSend = async () => {
    const timeoutPromise = (ms, promise) => {
      return Promise.race([
        promise,
        new Promise((_, reject) => setTimeout(() => reject(new Error('ENS resolution timed out')), ms))
      ]);
    };

    if (to && amount) {
      let resolvedTo = to
      if (to.endsWith('.eth')) {
        try {
          resolvedTo = await timeoutPromise(5000, client.getEnsAddress({ name: normalize(to) }));
          if (!resolvedTo) {
            throw new Error(`ENS name ${to} could not be resolved`);
          }
        } catch (err) {
          console.error('ENS resolution failed:', err.message)
          setRejectionError(err.message);
          return;
        }
      }
      try {
        clearMessages()
        await sendTransactionAsync({
          to: resolvedTo,
          value: parseEther(amount),
          chainId,
          account: address,
        })
        console.log('Transaction sent:', { to: resolvedTo, amount, address, hash })
      } catch (err) {
        if (err.name === 'UserRejectedRequestError' || err.message.includes('rejected')) {
          setRejectionError('Transaction rejected in wallet.')
        } else {
          setRejectionError(`Transaction error: ${err.message}`)
        }
        console.error('Transaction failed:', err.message)
      }
    }
    if (error) console.error('Transaction failed:', error.message)
  }

  useEffect(() => {
    if (isConnected && !hasInitialSwitch && chainId !== mainnet.id) {
      setHasInitialSwitch(true)
      switchChain({ chainId: mainnet.id })
    }
  }, [isConnected, hasInitialSwitch, chainId, switchChain])

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg shadow-lg text-center">
        <h1 className="text-2xl font-bold mb-4">Simple Web3 App</h1>
        {!isConnected ? (
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded"
            onClick={() => connect({ connector: connectors[0] })}
          >
            {isLoading ? 'Connecting...' : 'Connect Wallet'}
          </button>
        ) : (
          <div>
            <input
              type="text"
              placeholder="ENS name or address (e.g., vitalik.eth)"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="border p-2 mb-2 w-full"
            />
            <input
              type="number"
              placeholder="ETH amount (e.g., 0.01)"
              value={amount}
              step="any"
              onChange={(e) => setAmount(e.target.value)}
              className="border p-2 mb-2 w-full"
            />
            <button
              disabled={isPending}
              className="bg-green-500 text-white px-4 py-2 rounded"
              onClick={handleSend}
            >
              {isPending ? 'Sending...' : 'Send ETH'}
            </button>
            <div className="mt-4">
              Current Network:
              <select
                value={chainId}
                onChange={(e) => switchChain({ chainId: Number(e.target.value) })}
                className="ml-2 border p-1"
              >
                {chains.map((chain) => (
                  <option key={chain.id} value={chain.id}>{chain.name}</option>
                ))}
              </select>
            </div>
            {isConfirming && <div>Waiting for confirmation...</div>}
            {isConfirmed && <div>Transaction confirmed.</div>}            
            {hash && (
              <div className="mt-2 text-green-500">
                View transaction on <a href={`https://${chainSlug}.blockscout.com/tx/${hash}`} target="_blank" rel="noopener noreferrer" className="underline">Blockscout</a>
              </div>
            )}
            {rejectionError && (
              <div className="mt-2 text-red-500">
                {rejectionError}
              </div>
            )}
            {error && <div className="text-red-500">{error.message}</div>}
          </div>
        )}
      </div>
    </div>
  )
}