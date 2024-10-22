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
import MEV_commons.databases as databases
import src.constants as constants


async def enforce_total_databases_max_size():
    if constants.ENABLE_RUN_DATABASE_LIMIT:
        run_databases_identifier = databases.RunDatabasesProvider.instance().get_any_run_databases_identifier()
        pruner = databases.run_databases_pruner_factory(
            run_databases_identifier,
            constants.MAX_TOTAL_RUN_DATABASES_SIZE,
        )
        await pruner.explore()
        await pruner.prune_oldest_run_databases()
