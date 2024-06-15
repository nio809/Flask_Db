from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import mysql.connector
from mysql.connector import Error, pooling
import json

app = Flask(__name__)
CORS(app)  # Enable CORS on the Flask app

# Define the connection pool
def init_connection_pool():
    try:
        pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            pool_reset_session=True,
            host='sql5.freesqldatabase.com',
            user='___',
            password='____',
            database='____'
        )
        return pool
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

connection_pool = init_connection_pool()



def get_connection():
    """Get a connection from the pool."""
    try:
        return connection_pool.get_connection()
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

def add_user(connection, userid, wallet, powerups):
    query = """
    INSERT INTO Users (userid, wallet, powerup1, powerup2, powerup3, powerup4, powerup5, powerup6)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor = connection.cursor()
    cursor.execute(query, (userid, wallet, *powerups))
    connection.commit()

def add_score(connection, userid, score):
    query = "INSERT INTO Scores (userid, score) VALUES (%s, %s)"
    cursor = connection.cursor()
    cursor.execute(query, (userid, score))
    connection.commit()
    print(f"Score {score} added for userid {userid}")

def fetch_scores_by_userid(connection, userid):
    """Fetch all scores for a specific userid."""
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT userid, score FROM Scores WHERE userid = %s", (userid,))
    rows = cursor.fetchall()
    return json.dumps(rows, default=str)

def fetch_all_scores(connection):
    """Fetch all scores for all users."""
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT userid, score FROM Scores")
    rows = cursor.fetchall()
    return json.dumps(rows, default=str)

@app.route('/scores', methods=['GET'])
def handle_fetch_scores():
    """Endpoint to fetch scores for all users."""
    connection = get_connection()
    if connection:
        try:
            scores = fetch_all_scores(connection)
            return scores, 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/scores/<userid>', methods=['GET'])
def handle_fetch_scores_by_userid(userid):
    """Endpoint to fetch scores for a specific userid."""
    connection = get_connection()
    if connection:
        try:
            scores = fetch_scores_by_userid(connection, userid)
            return scores, 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    return jsonify({'error': 'Database connection failed'}), 500

def add_or_update_user(connection, userid, wallet, powerups):
    cursor = connection.cursor()
    # Check if user exists
    cursor.execute("SELECT * FROM Users WHERE userid = %s", (userid,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        # Update existing user
        cursor.execute("""
            UPDATE Users SET 
            wallet = %s, 
            powerup1 = powerup1 + %s, 
            powerup2 = powerup2 + %s, 
            powerup3 = powerup3 + %s, 
            powerup4 = powerup4 + %s, 
            powerup5 = powerup5 + %s, 
            powerup6 = powerup6 + %s
            WHERE userid = %s
        """, (wallet, *powerups, userid))
    else:
        # Insert new user
        query = """
        INSERT INTO Users (userid, wallet, powerup1, powerup2, powerup3, powerup4, powerup5, powerup6)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (userid, wallet, *powerups))
    
    connection.commit()

def add_score(connection, userid, score):
    query = "INSERT INTO Scores (userid, score) VALUES (%s, %s)"
    cursor = connection.cursor()
    cursor.execute(query, (userid, score))
    connection.commit()
    print(f"Score {score} added for userid {userid}")

@app.route('/add_user', methods=['POST'])
def handle_add_or_update_user():
    data = request.json
    userid = data['userid']
    wallet = data['wallet']
    powerups = data['powerups']
    connection = get_connection()
    if connection:
        try:
            add_or_update_user(connection, userid, wallet, powerups)
            return jsonify({'user_id': userid}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    else:
        return jsonify({'error': 'Database connection failed'}), 500



@app.route('/reduce_powerups/<userid>', methods=['POST'])
def reduce_powerups(userid):
    data = request.json
    powerups_to_reduce = data['powerups']  #hehe Expect a list of integers to reduce each powerup
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE Users SET 
                powerup1 = powerup1 - %s, 
                powerup2 = powerup2 - %s, 
                powerup3 = powerup3 - %s, 
                powerup4 = powerup4 - %s, 
                powerup5 = powerup5 - %s, 
                powerup6 = powerup6 - %s
                WHERE userid = %s
            """, (*powerups_to_reduce, userid))
            connection.commit()
            return jsonify({'message': 'Powerups reduced successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    else:
        return jsonify({'error': 'Database connection failed'}), 500


@app.route('/top_users', methods=['GET'])
def handle_top_users():
    """Endpoint to fetch the top 10 users with the highest scores."""
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT userid, SUM(score) AS total_score
            FROM Scores
            GROUP BY userid
            ORDER BY total_score DESC
            LIMIT 10
            """
            cursor.execute(query)
            top_users = cursor.fetchall()
            return jsonify(top_users), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    return jsonify({'error': 'Database connection failed'}), 500


@app.route('/reduce_score', methods=['POST'])
def handle_reduce_score():
    """Endpoint to reduce a user's score."""
    data = request.json
    userid = data['userid']
    score_to_reduce = data['score']
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)  # Ensure dictionary results
            # Check if the user has enough points to deduct
            cursor.execute("SELECT SUM(score) as total_score FROM Scores WHERE userid = %s", (userid,))
            result = cursor.fetchone()
            if result and result['total_score'] >= score_to_reduce:
                # Deduct the score
                add_score(connection, userid, -score_to_reduce)
                return jsonify({'message': 'Score reduced successfully'}), 200
            else:
                return jsonify({'error': 'Not enough score to reduce'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/get_powerups/<userid>', methods=['GET'])
def get_powerups(userid):
    """Endpoint to fetch the first three powerups for a specific userid."""
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT powerup1, powerup2, powerup3 FROM Users WHERE userid = %s", (userid,))
            powerups = cursor.fetchone()
            if powerups:
                return jsonify(powerups), 200
            else:
                return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    else:
        return jsonify({'error': 'Database connection failed'}), 500
    
@app.route('/add_score', methods=['GET'])
def handle_add_score():
    userid = request.args.get('userid', default='No ID')
    score = request.args.get('score', type=int, default=0)
    connection = get_connection()
    if connection:
        try:
            add_score(connection, userid, score)
            return jsonify({'message': 'Score added successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    return jsonify({'error': 'Database connection failed'}), 500
def add_transaction(connection, txn, amount):
    """Insert a transaction into the Transaction table."""
    query = "INSERT INTO Transaction (Txn, Amount) VALUES (%s, %s)"
    cursor = connection.cursor()
    cursor.execute(query, (txn, amount))
    connection.commit()
    print(f"Transaction {txn} with amount {amount} added successfully")
@app.route('/add_transaction', methods=['POST'])
def handle_add_transaction():
    """Endpoint to add a new transaction."""
    data = request.json
    txn = data.get('txn')
    amount = data.get('amount')
    
    if not txn or not amount:
        return jsonify({'error': 'Missing transaction data'}), 400

    connection = get_connection()
    if connection:
        try:
            add_transaction(connection, txn, amount)
            return jsonify({'message': 'Transaction added successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    else:
        return jsonify({'error': 'Database connection failed'}), 500

def check_transaction_exists(connection, txn):
    """Check if a transaction exists in the database."""
    query = "SELECT COUNT(*) FROM Transaction WHERE Txn = %s"
    cursor = connection.cursor()
    cursor.execute(query, (txn,))
    result = cursor.fetchone()
    return result[0] > 0  # Returns True if the transaction exists, False otherwise
@app.route('/check_transaction/<txn>', methods=['GET'])
def handle_check_transaction(txn):
    """Endpoint to check if a transaction exists and return 'Y' for yes and 'N' for no."""
    connection = get_connection()
    if connection:
        try:
            exists = check_transaction_exists(connection, txn)
            return "Y" if exists else "N", 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    else:
        return jsonify({'error': 'Database connection failed'}), 500
def clear_transactions(connection):
    """Clear all transactions from the Transaction table."""
    query = "DELETE FROM Transaction"
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    print("All transactions have been cleared from the table.")
@app.route('/clear_transactions', methods=['POST'])  # Using POST to prevent accidental data loss
def handle_clear_transactions():
    """Endpoint to clear all transactions from the database."""
    connection = get_connection()
    if connection:
        try:
            clear_transactions(connection)
            return jsonify({'message': 'All transactions cleared successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                connection.close()
            except mysql.connector.errors.NotSupportedError:
                pass
    else:
        return jsonify({'error': 'Database connection failed'}), 500




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True) 

