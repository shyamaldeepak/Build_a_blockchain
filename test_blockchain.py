import time
import requests
import subprocess
import sys
import os
#-- Assume blockchain.py is in the same directory as this test script
def start_node(port):
    print(f"Starting node on port {port}...")
    # Use python executable relative to current env if possible, or just 'python'
    process = subprocess.Popen([sys.executable, 'blockchain.py', str(port)], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
    return process
# Main test function
def test_blockchain():
    node1_port = 5001
    node2_port = 5002
    
    node1_url = f"http://127.0.0.1:{node1_port}"
    node2_url = f"http://127.0.0.1:{node2_port}"

    p1 = start_node(node1_port)
    p2 = start_node(node2_port)

    try:
        print("Waiting for nodes to initialize...")
        time.sleep(5) 

        # 1. Mine block on Node 1
        print("\n[Node 1] Mining block 1...")
        resp = requests.get(f"{node1_url}/mine_block")
        print(f"Response: {resp.status_code} - {resp.json()['message']}")
        assert resp.status_code == 200

        # 2. Add Transaction on Node 1
        print("\n[Node 1] Adding transaction...")
        tx_data = {'sender': 'Alice', 'receiver': 'Bob', 'amount': 10}
        resp = requests.post(f"{node1_url}/add_transaction", json=tx_data)
        print(f"Response: {resp.status_code} - {resp.json()['message']}")
        assert resp.status_code == 201

        # 3. Mine block on Node 1 (to confirm transaction)
        print("\n[Node 1] Mining block 2 (confirming transaction)...")
        resp = requests.get(f"{node1_url}/mine_block")
        data = resp.json()
        print(f"Response: {resp.status_code} - Block Index: {data['index']}")
        # Verify transaction is in the block (or previous block depending on implementation logic, but usually current mined block includes pending txs)
        # In our implementation: create_block adds currently pending transactions.
        # So this new block should have the transaction.
        txs = data['transactions']
        assert any(t['sender'] == 'Alice' for t in txs), "Transaction not found in mined block!"
        print("Transaction confirmed in block!")

        # 4. Connect Node 2 to Node 1
        print(f"\n[Node 2] Connecting to Node 1 ({node1_url})...")
        nodes = {'nodes': [node1_url]}
        resp = requests.post(f"{node2_url}/connect_node", json=nodes)
        print(f"Response: {resp.status_code} - {resp.json()['message']}")
        assert resp.status_code == 201

        # 5. Check Node 2 Chain (should be short)
        print("\n[Node 2] Initial chain check...")
        resp = requests.get(f"{node2_url}/get_chain")
        len_node2 = resp.json()['length']
        print(f"Node 2 Length: {len_node2}")

        # 6. Consensus on Node 2
        print("\n[Node 2] Resolving conflicts (Consensus)...")
        resp = requests.get(f"{node2_url}/replace_chain")
        print(f"Response: {resp.status_code} - {resp.json()}")
        
        # 7. Verify Node 2 Updated
        resp = requests.get(f"{node2_url}/get_chain")
        new_len_node2 = resp.json()['length']
        print(f"Node 2 Length after consensus: {new_len_node2}")
        
        # Node 1 has mined 2 blocks + genesis = 3 blocks? 
        # Wait, __init__ creates genesis.
        # Mine block 1 -> length 2.
        # Mine block 2 -> length 3.
        # Node 2 starts with genesis -> length 1.
        # After consensus, Node 2 should have length 3.
        
        # Let's check Node 1 length
        resp1 = requests.get(f"{node1_url}/get_chain")
        len_node1 = resp1.json()['length']
        
        assert new_len_node2 == len_node1, f"Consensus failed! Node 1 len: {len_node1}, Node 2 len: {new_len_node2}"
        print(f"SUCCESS! Node 2 synchronized with Node 1 (Length: {new_len_node2})")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        # Print stdout/stderr if failed
        print("Node 1 Output:", p1.stdout.read())
        print("Node 2 Output:", p2.stdout.read())
        
    finally:
        print("\nShutting down nodes...")
        p1.terminate()
        p2.terminate()

if __name__ == "__main__":
    test_blockchain()
