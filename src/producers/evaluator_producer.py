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
import MEV_commons.enums as common_enums

import MEV_backtesting.api as backtesting_api

import MEV_evaluators.api as evaluator_api
import MEV_evaluators.MEV_channel_consumer as evaluator_channel_consumer

import src.channels as MEV_channel
import src.logger as logger


class EvaluatorProducer(MEV_channel.MEVChannelProducer):
    """EvaluatorFactory class:
    - Create evaluators
    """

    def __init__(self, channel, MEV):
        super().__init__(channel)
        self.MEV = MEV
        self.tentacles_setup_config = self.MEV.tentacles_setup_config

        self.matrix_id = None

    async def start(self):
        await evaluator_api.initialize_evaluators(self.MEV.config, self.tentacles_setup_config)
        self.matrix_id = evaluator_api.create_matrix()
        await evaluator_api.create_evaluator_channels(
            self.matrix_id, is_backtesting=backtesting_api.is_backtesting_enabled(self.MEV.config)
        )
        await logger.init_evaluator_chan_logger(self.matrix_id)

    async def create_evaluators(self, exchange_configuration):
        await self.send(bot_id=self.MEV.bot_id,
                        subject=common_enums.MEVChannelSubjects.CREATION.value,
                        action=evaluator_channel_consumer.MEVChannelEvaluatorActions.EVALUATOR.value,
                        data={
                            evaluator_channel_consumer.MEVChannelEvaluatorDataKeys.TENTACLES_SETUP_CONFIG.value:
                                self.MEV.tentacles_setup_config,
                            evaluator_channel_consumer.MEVChannelEvaluatorDataKeys.MATRIX_ID.value:
                                self.MEV.evaluator_producer.matrix_id,
                            evaluator_channel_consumer.MEVChannelEvaluatorDataKeys.EXCHANGE_CONFIGURATION.value:
                                exchange_configuration
                        })

    async def stop(self):
        self.logger.debug("Stopping ...")
        await evaluator_api.stop_all_evaluator_channels(self.matrix_id)
        self.logger.debug("Stopped")
