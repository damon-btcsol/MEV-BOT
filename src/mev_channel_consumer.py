#  This file is part of MEV (https://github.com/Drakkar-Software/MEV)
#  Copyright (c) 2023 Drakkar-Software, All rights reserved.
#
#  MEV is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  MEV is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with MEV. If not, see <https://www.gnu.org/licenses/>.
import async_channel.channels as channel_instances
import async_channel.util as channel_creator

import MEV_commons.enums as enums
import MEV_commons.logging as logging

import MEV_evaluators.MEV_channel_consumer as evaluator_channel_consumer

import MEV_services.MEV_channel_consumer as service_channel_consumer

import MEV_trading.api as trading_api
import MEV_trading.MEV_channel_consumer as trading_channel_consumer

import src.channels as MEV_channel
import src.logger as logger


class MEVChannelGlobalConsumer:

    def __init__(self, MEV):
        self.MEV = MEV
        self.logger = logging.get_logger(self.__class__.__name__)

        # the list of MEV channel consumers
        self.MEV_channel_consumers = []

        # the MEV Channel instance
        self.MEV_channel = None

    async def initialize(self):
        # Creates MEV Channel
        self.MEV_channel: MEV_channel.MEVChannel = await channel_creator.create_channel_instance(
            MEV_channel.MEVChannel, channel_instances.set_chan_at_id,
            is_synchronized=True, bot_id=self.MEV.bot_id)

        # Initialize global consumer
        self.MEV_channel_consumers.append(
            await self.MEV_channel.new_consumer(self.MEV_channel_callback, bot_id=self.MEV.bot_id))

        # Initialize trading consumer
        self.MEV_channel_consumers.append(
            await self.MEV_channel.new_consumer(
                trading_channel_consumer.MEV_channel_callback,
                bot_id=self.MEV.bot_id,
                action=[action.value for action in trading_channel_consumer.MEVChannelTradingActions]
            ))

        # Initialize evaluator consumer
        self.MEV_channel_consumers.append(
            await self.MEV_channel.new_consumer(
                evaluator_channel_consumer.MEV_channel_callback,
                bot_id=self.MEV.bot_id,
                action=[action.value for action in evaluator_channel_consumer.MEVChannelEvaluatorActions]
            ))

        # Initialize service consumer
        self.MEV_channel_consumers.append(
            await self.MEV_channel.new_consumer(
                service_channel_consumer.MEV_channel_callback,
                bot_id=self.MEV.bot_id,
                action=[action.value for action in service_channel_consumer.MEVChannelServiceActions]
            ))

    async def MEV_channel_callback(self, bot_id, subject, action, data) -> None:
        """
        MEV channel consumer callback
        :param bot_id: the callback bot id
        :param subject: the callback subject
        :param action: the callback action
        :param data: the callback data
        """
        if subject == enums.MEVChannelSubjects.NOTIFICATION.value:
            if action == trading_channel_consumer.MEVChannelTradingActions.EXCHANGE.value:
                if trading_channel_consumer.MEVChannelTradingDataKeys.EXCHANGE_ID.value in data:
                    exchange_id = data[trading_channel_consumer.MEVChannelTradingDataKeys.EXCHANGE_ID.value]
                    self.MEV.exchange_producer.register_created_exchange_id(exchange_id)
                    await logger.init_exchange_chan_logger(exchange_id)
                    exchange_configuration = trading_api.get_exchange_configuration_from_exchange_id(exchange_id)
                    await self.MEV.evaluator_producer.create_evaluators(exchange_configuration)
                    # If an exchange is created before interface producer is done, it will be registered via
                    # self.MEV.interface_producer directly on creation
                    await self.MEV.interface_producer.register_exchange(exchange_id)
            elif action == evaluator_channel_consumer.MEVChannelEvaluatorActions.EVALUATOR.value:
                if not self.MEV.service_feed_producer.started:
                    # Start service feeds now that evaluators registered their feed requirements
                    await self.MEV.service_feed_producer.start_feeds()
            elif action == service_channel_consumer.MEVChannelServiceActions.INTERFACE.value:
                await self.MEV.interface_producer.register_interface(
                    data[service_channel_consumer.MEVChannelServiceDataKeys.INSTANCE.value])
            elif action == service_channel_consumer.MEVChannelServiceActions.NOTIFICATION.value:
                await self.MEV.interface_producer.register_notifier(
                    data[service_channel_consumer.MEVChannelServiceDataKeys.INSTANCE.value])
            elif action == service_channel_consumer.MEVChannelServiceActions.SERVICE_FEED.value:
                await self.MEV.service_feed_producer.register_service_feed(
                    data[service_channel_consumer.MEVChannelServiceDataKeys.INSTANCE.value])

    async def stop(self) -> None:
        """
        Remove all MEV Channel consumers
        """
        for consumer in self.MEV_channel_consumers:
            await self.MEV_channel.remove_consumer(consumer)
