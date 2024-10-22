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
import asyncio

import MEV_commons.enums as common_enums
import MEV_commons.constants as common_constants

import MEV_trading.api as trading_api
import MEV_trading.MEV_channel_consumer as trading_channel_consumer

import src.channels as MEV_channel


class ExchangeProducer(MEV_channel.MEVChannelProducer):
    def __init__(self, channel, MEV, backtesting, ignore_config=False):
        super().__init__(channel)
        self.MEV = MEV
        self.ignore_config = ignore_config

        self.backtesting = backtesting
        self.exchange_manager_ids = []

        self.to_create_exchanges_count = 0
        self.created_all_exchanges = asyncio.Event()

    async def start(self):
        self.to_create_exchanges_count = 0
        self.created_all_exchanges.clear()
        for exchange_name in trading_api.get_enabled_exchanges_names(self.MEV.config):
            await self.create_exchange(exchange_name, self.backtesting)
            self.to_create_exchanges_count += 1

    def register_created_exchange_id(self, exchange_id):
        self.exchange_manager_ids.append(exchange_id)
        if len(self.exchange_manager_ids) == self.to_create_exchanges_count:
            self.created_all_exchanges.set()
            self.logger.debug(f"Exchange(s) created")

    async def stop(self):
        self.logger.debug("Stopping ...")
        for exchange_manager in trading_api.get_exchange_managers_from_exchange_ids(self.exchange_manager_ids):
            await trading_api.stop_exchange(exchange_manager)
        self.logger.debug("Stopped")

    async def create_exchange(self, exchange_name, backtesting):
        await self.send(bot_id=self.MEV.bot_id,
                        subject=common_enums.MEVChannelSubjects.CREATION.value,
                        action=trading_channel_consumer.MEVChannelTradingActions.EXCHANGE.value,
                        data={
                            trading_channel_consumer.MEVChannelTradingDataKeys.TENTACLES_SETUP_CONFIG.value:
                                self.MEV.tentacles_setup_config,
                            trading_channel_consumer.MEVChannelTradingDataKeys.MATRIX_ID.value:
                                self.MEV.evaluator_producer.matrix_id,
                            trading_channel_consumer.MEVChannelTradingDataKeys.BACKTESTING.value: backtesting,
                            trading_channel_consumer.MEVChannelTradingDataKeys.EXCHANGE_CONFIG.value:
                                self.MEV.config,
                            trading_channel_consumer.MEVChannelTradingDataKeys.EXCHANGE_NAME.value: exchange_name,
                        })
