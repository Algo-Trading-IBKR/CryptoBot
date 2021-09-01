from pymongo import MongoClient
from python_on_whales import DockerClient

env_file = "variables.env"

def main():
    try:
        mongo_connect_url = "mongodb://db_admin:qrXp0HtVfWDH1otKSZM9HiC8m838Ud5u@192.168.50.69:27017/cryptobot?authSource=admin"

        Mongo = MongoClient(mongo_connect_url)

        user_configs = Mongo.cryptobot.users.find({ "active": True })

        dockerfile = open("./bot/docker-compose.yml", "w")

        dockercompose = '''version: "3.8"\nservices:\n  '''
        for user in user_configs:
            dockercompose += f"""\n  cryptobot-{user['name'].lower()}_{user['_id']}:
    build: .
    environment:
        ACTIVE_CONFIG: {user['name']}_{user['_id']}
    env_file:
        - {env_file}
    restart: always
    volumes:
        - ./logs:/app/logs
    networks:
        - shared"""

        dockercompose += "\n\n"
        dockercompose += """networks:
            shared:
                name: shared
                driver: bridge"""

        dockerfile.write(dockercompose)

        dockerfile.close()

        docker = DockerClient(compose_files=["./bot/mongo/docker-compose.yml"])
        docker.compose.down(remove_orphans=True)
        docker = DockerClient(compose_files=["./bot/docker-compose.yml"])
        docker.compose.down(remove_orphans=True)

        docker = DockerClient(compose_files=["./bot/mongo/docker-compose.yml"])
        docker.compose.down(remove_orphans=True)
        docker.compose.build()
        docker.compose.up(detach=True)

        docker = DockerClient(compose_files=["./bot/docker-compose.yml"])
        docker.compose.down(remove_orphans=True)
        docker.compose.build()
        docker.compose.up(detach=True)
        
    except Exception as e:
        print(str(e))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e))
