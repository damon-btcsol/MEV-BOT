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
import src.community.models.community_donation as community_donation
import MEV_commons.support as support


class CommunitySupports(support.Support):
    DEFAULT_SUPPORT_ROLE = "default"
    MEV_DONOR_ROLE = "donor"

    def __init__(self, support_role: str = None, donations: list = None):
        self.support_role = support_role or CommunitySupports.DEFAULT_SUPPORT_ROLE
        self.donations = donations or []

    def is_supporting(self) -> bool:
        return self.support_role != self.DEFAULT_SUPPORT_ROLE or self.is_donor()

    def is_donor(self) -> bool:
        return self.support_role == self.MEV_DONOR_ROLE or bool(self.donations)

    @staticmethod
    def from_community_dict(data):
        return CommunitySupports(
            data["data"]["attributes"].get("support_role", CommunitySupports.DEFAULT_SUPPORT_ROLE),
            [community_donation.CommunityDonation.from_community_dict(donation_data)
             for donation_data in data.get("included", [])]
        )
