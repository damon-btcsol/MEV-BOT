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
import MEV_backtesting.api as backtesting_api

import MEV_commons.enums as common_enums

import MEV_services.api as service_api
import MEV_services.MEV_channel_consumer as service_channel_consumer

import MEV_tentacles_manager.api as tentacles_manager_api

import src.channels as MEV_channels
import src.constants as constants


class ServiceFeedProducer(MEV_channels.MEVChannelProducer):
    """EvaluatorFactory class:
    - Create service feeds
    """

    def __init__(self, channel, MEV):
        super().__init__(channel)
        self.MEV = MEV
        self.started = False

        self.service_feeds = []

    async def start(self):
        in_backtesting = backtesting_api.is_backtesting_enabled(self.MEV.config)
        service_feed_factory = service_api.create_service_feed_factory(self.MEV.config,
                                                                       self.MEV.async_loop,
                                                                       self.MEV.bot_id)
        for feed in service_feed_factory.get_available_service_feeds(in_backtesting):
            if tentacles_manager_api.is_tentacle_activated_in_tentacles_setup_config(
                    self.MEV.tentacles_setup_config, feed.get_name()):
                await self.create_feed(service_feed_factory, feed, in_backtesting)

    async def start_feeds(self):
        self.started = True
        for feed in self.service_feeds:
            await self.send(bot_id=self.MEV.bot_id,
                            subject=common_enums.MEVChannelSubjects.UPDATE.value,
                            action=service_channel_consumer.MEVChannelServiceActions.START_SERVICE_FEED.value,
                            data={
                                service_channel_consumer.MEVChannelServiceDataKeys.INSTANCE.value: feed,
                                service_channel_consumer.MEVChannelServiceDataKeys.EDITED_CONFIG.value:
                                    self.MEV.get_edited_config(constants.CONFIG_KEY, dict_only=False)
                            })

    async def create_feed(self, service_feed_factory, feed, in_backtesting):
        await self.send(bot_id=self.MEV.bot_id,
                        subject=common_enums.MEVChannelSubjects.CREATION.value,
                        action=service_channel_consumer.MEVChannelServiceActions.SERVICE_FEED.value,
                        data={
                            service_channel_consumer.MEVChannelServiceDataKeys.EDITED_CONFIG.value:
                                self.MEV.get_edited_config(constants.CONFIG_KEY, dict_only=False),
                            service_channel_consumer.MEVChannelServiceDataKeys.BACKTESTING_ENABLED.value:
                                in_backtesting,
                            service_channel_consumer.MEVChannelServiceDataKeys.CLASS.value: feed,
                            service_channel_consumer.MEVChannelServiceDataKeys.FACTORY.value: service_feed_factory
                        })

    async def register_service_feed(self, instance):
        self.service_feeds.append(instance)

    async def stop(self):
        self.logger.debug("Stopping ...")
        for service_feed in self.service_feeds:
            await service_api.stop_service_feed(service_feed)
        self.logger.debug("Stopped")
