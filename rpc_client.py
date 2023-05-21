import asyncio


async def main():
    from app.config import Config
    from app.rabbit import Rabbit, RPCClient
    rabbit = Rabbit(Config.RABBITMQ_URI)
    await rabbit.connect()
    fibonacci_rpc = await RPCClient(
        rabbit=rabbit,
        publish_routing_key="test_q"
    ).start()

    print(" [x] Requesting fib(30)")

    response = await fibonacci_rpc.call(30)

    print(f" [.] Got {response!r}")


if __name__ == '__main__':
    asyncio.run(main())
